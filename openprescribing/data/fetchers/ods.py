import datetime
import json
import logging
import tempfile

import duckdb

from openprescribing.data.utils.duckdb_utils import escape
from openprescribing.data.utils.filename_utils import get_temp_filename_for
from openprescribing.data.utils.http_session import HTTPSession


log = logging.getLogger(__name__)


def fetch(directory):
    dataset_dir = directory / "ods"

    # The ODS data is updated nightly, but we don't need updates that frequently so
    # instead we just pretend that it's published on the first of the month and only
    # download if we're in a new month.
    latest_file = max(dataset_dir.glob("*.parquet"), default=None)
    if latest_file:
        date_str = latest_file.name[4:][:10]
        latest_month = datetime.date.fromisoformat(date_str).replace(day=1)
        if latest_month >= datetime.date.today().replace(day=1):
            log.debug(f"Already fetched a file for this month: {latest_file.name}")
            return

    filename = dataset_dir / f"ods_{datetime.date.today()}.parquet"

    # Web interface available at:
    # https://www.odsdatasearchandexport.nhs.uk/
    log.info("Fetching latest ODS export")
    http = HTTPSession(
        "https://www.odsdatasearchandexport.nhs.uk/api/",
        log=log.info,
    )
    response = http.post(
        "search/organisationReportSearch",
        json={
            "searchQueryPrimaryRoleCodes": ",".join(
                # Full list of role codes available at:
                # https://directory.spineservices.nhs.uk/ORD/2-0-0/roles
                [
                    # PRESCRIBING COST CENTRE
                    # Includes GP practices, plus a whole load of other organisation
                    # types for which we have prescribing data
                    "RO177",
                    #
                    # PRIMARY CARE NETWORK
                    "RO272",
                    #
                    # CLINICAL COMMISSIONING GROUP
                    # SICBLs still have this as their primary role name, though they
                    # also have their new name as a non-primary role
                    "RO98",
                    #
                    # STRATEGIC PARTNERSHIP
                    # ICBs still have this as their primary role name, though they
                    # also have their new name as a non-primary role
                    "RO261",
                    #
                    # NHS ENGLAND (REGION)
                    "RO209",
                ]
            ),
            "searchQueryIsActive": "All (Status)",
            "offset": 0,
            "batchSize": 100000,
        },
    )

    orgs = response.json()["orgArray"]

    # In 2026-03 we observed Practices and Others attached to multiple PCNs, as they
    # were due to change PCN at the end of month (i.e. starting new PCN on 2026-04-01).
    # At the time, the `organisationReportSearch` endpoint returned incomplete data
    # for this change. It included multiple PCNs for e.g. a Practice, but not the
    # relevant dates, so we have no way to choose between them.
    # The `singleOrganisationSearchByCode` endpoint does have these dates in the
    # `relationships` key, so enrich `org` with that extra info for all PCNs.
    for org in orgs:
        # Role RO272 means PCNs
        if not org["primaryRole"] == "RO272":
            continue

        # Occasionally (once per import) this returns HTTP 500, but typically works on an
        # immediate retry.
        response = http.get(
            f"search/singleOrganisationSearchByCode?code={org['id']}", 3
        )
        pcn = response.json()

        # Default to empty dict for historic PCNs with no current relationships
        org["relationships"] = pcn.get("relationships", {})

    filename.parent.mkdir(parents=True, exist_ok=True)
    tmp_filename = get_temp_filename_for(filename)
    json_to_parquet(orgs, tmp_filename)
    tmp_filename.replace(filename)
    log.info(f"Saved: {filename.name}")


def json_to_parquet(json_array, filename):
    # The easiest and most efficient way to capture the API results is to let DuckDB
    # convert the JSON response to a Parquet file, but to do this we need to write the
    # JSON to a file.
    with tempfile.NamedTemporaryFile("w+t") as f:
        json.dump(json_array, f)
        f.flush()
        # Use `auto_detect` to get DuckDB to infer the correct Parquet types based on
        # the contents of the JSON. Use `sample_size = -1` to have this based on the
        # entire file contents and not just an initial sample.
        duckdb.sql(
            f"""
            COPY (
                SELECT * FROM
                read_json(
                  {escape(f.name)},
                  auto_detect = true,
                  sample_size = -1
                )
            )
            TO {escape(filename)} (
                FORMAT 'PARQUET',
                PARQUET_VERSION V2,
                CODEC 'zstd',
                COMPRESSION_LEVEL 10
            );
            """,
        )
