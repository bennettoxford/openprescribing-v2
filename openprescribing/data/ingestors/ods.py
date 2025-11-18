import logging

import duckdb
from django.conf import settings
from django.db import transaction

from openprescribing.data.models import IngestedFile, Org
from openprescribing.data.utils.duckdb_utils import escape


log = logging.getLogger(__name__)


def ingest():
    ods_files = settings.DOWNLOAD_DIR.glob("ods/*.parquet")
    latest_file = max(ods_files, default=None)

    if not latest_file or latest_file.name <= IngestedFile.get_by_name("ods"):
        log.debug("Found no new data to ingest")
        return

    log.info(f"Preparing to ingest file: {latest_file.name}")

    conn = duckdb.connect()
    conn.sql(f"CREATE VIEW ods AS SELECT * FROM read_parquet({escape(latest_file)})")

    with transaction.atomic(using="data"):
        Org.objects.all().delete()
        ingest_ods(conn)
        IngestedFile.set_by_name("ods", latest_file.name)

    conn.close()

    count = Org.objects.count()
    log.info(f"Ingested {count} organisations")


def ingest_ods(conn):
    OrgType = Org.OrgType

    ORG_TYPE_QUERIES = {
        OrgType.REGION: "primaryRoleName = 'NHS ENGLAND (REGION)'",
        OrgType.ICB: "'INTEGRATED CARE BOARD' IN roleName",
        OrgType.SICBL: "'SUB ICB LOCATION' IN roleName AND 'ICB COMMISSIONING PROXY' NOT IN roleName",
        OrgType.PCN: "primaryRoleName = 'PRIMARY CARE NETWORK'",
        OrgType.PRACTICE: "'GP PRACTICE' IN roleName",
        OrgType.OTHER: "primaryRoleName = 'PRESCRIBING COST CENTRE' AND 'GP PRACTICE' NOT IN roleName",
    }

    known_ids = set()

    for org_type in OrgType:
        if org_type == OrgType.NATION:
            continue

        log.info(f"Ingesting {org_type!r}")
        where_clause = ORG_TYPE_QUERIES[org_type]
        results = conn.execute(
            f"""
            SELECT
                id, name, inactive,
                -- Combine the various fields which may contain related orgs IDs into a single list
                isPartnerToCode || [PCO, ICB, NHSER] AS related_ids
            FROM
                ods
            WHERE
                country = 'ENGLAND' AND ({where_clause})
            """
        )

        rows = results.fetchall()
        assert rows, f"No orgs of type {org_type!r} found – aborting"

        for id_, name, inactive, related_ids in rows:
            org = Org.objects.create(
                id=id_, org_type=org_type, name=name, inactive=inactive
            )
            # The relations we get in the data don't specify the parent/child direction.
            # However by creating orgs in strictly hierarchical order, and by only
            # creating relationships where the target already exists we know that all
            # the relationships are child->parent.
            parent_ids = known_ids.intersection(related_ids)
            org.parents.add(*parent_ids)
            known_ids.add(id_)

    # Create a "dummy" organisation to represent all of NHS England and set it as the
    # parent of each of the regions. This avoids needing special logic elsewhere to
    # handle national totals.
    nation = Org.objects.create(
        id="ENGLAND", org_type=OrgType.NATION, name="NHS England", inactive=False
    )
    for region in Org.objects.filter(org_type=OrgType.REGION):
        region.parents.add(nation)
