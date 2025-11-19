import datetime
import logging
import re

from openprescribing.data.utils.filename_utils import get_latest_files_by_date
from openprescribing.data.utils.http_session import HTTPSession
from openprescribing.data.utils.remote_csv_utils import remote_zipped_csv_to_parquet


log = logging.getLogger(__name__)


def fetch(directory):
    fetch_dataset(
        directory,
        dataset_id="english-prescribing-dataset-epd-with-snomed-code",
        version_number=3,
    )
    fetch_dataset(
        directory,
        dataset_id="english-prescribing-data-epd",
        version_number=2,
    )


def fetch_dataset(directory, dataset_id, version_number):
    dataset_dir = directory / "prescribing"
    existing_files = dataset_dir.glob("*")

    http = HTTPSession(
        "https://opendata.nhsbsa.net/api/3/",
        # We start with DEBUG level logging while we're checking if there's anything new
        # to fetch
        log=log.debug,
    )
    response = http.get(
        "action/package_show",
        params={"id": dataset_id},
    )
    response_data = response.json()

    items_to_fetch = get_items_to_fetch(existing_files, response_data, version_number)

    # Any requests we now make will be to fetch new files so we log at INFO level
    http.log = log.info

    for item_id, output_filename in items_to_fetch:
        item_resp = http.get("action/resource_show", params={"id": item_id})
        zip_url = item_resp.json()["result"]["zip_url"]
        remote_zipped_csv_to_parquet(
            http, zip_url, dataset_dir / output_filename, encoding="latin-1"
        )
        log.info(f"Saved as: {output_filename}")


def get_items_to_fetch(existing_files, response_data, version_number):
    files_by_date = get_latest_files_by_date(existing_files)
    resources = response_data["result"]["resources"]

    to_fetch = []
    already_fetched = 0
    total = 0
    for item in sorted(resources, key=lambda i: i["name"]):
        year_month = re.match(r"^EPD_(?:SNOMED_)?(\d{6})$", item["name"]).group(1)
        date = datetime.date.fromisoformat(f"{year_month}01")
        published_at = datetime.datetime.fromisoformat(
            # Oddly `last_modified` is sometimes null (maybe before the first update?)
            # so we have to use the `created` date
            item["last_modified"] or item["created"]
        )

        # We use version numbers to distinguish the different structures in which
        # prescribing data has historically been published.
        filename = (
            f"prescribing_{date}_v{version_number}_{published_at:%Y-%m-%dT%H%M}.parquet"
        )

        if date in files_by_date and files_by_date[date].name >= filename:
            already_fetched += 1
        else:
            to_fetch.append((item["id"], filename))

        total += 1

    # Use INFO where there are new files to fetch, DEBUG otherwise
    (log.info if to_fetch else log.debug)(
        f"Found {total} files: {already_fetched} already fetched and "
        f"{len(to_fetch)} to fetch"
    )

    return to_fetch
