import datetime
import logging
import re
import tempfile
from pathlib import Path

from openprescribing.data.utils.csv_to_parquet import csv_to_parquet
from openprescribing.data.utils.filename_utils import (
    get_latest_files_by_date,
    get_temp_filename_for,
)
from openprescribing.data.utils.http_session import HTTPSession
from openprescribing.data.utils.zipfile_utils import extract_file_from_zip_archive


log = logging.getLogger(__name__)


def fetch(directory):
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
        params={"id": "english-prescribing-dataset-epd-with-snomed-code"},
    )
    response_data = response.json()

    items_to_fetch = get_items_to_fetch(existing_files, response_data)

    # Any requests we now make will be to fetch new files so we log at INFO level
    http.log = log.info

    for item_id, output_filename in items_to_fetch:
        item_resp = http.get("action/resource_show", params={"id": item_id})
        zip_url = item_resp.json()["result"]["zip_url"]
        remote_zipped_csv_to_parquet(
            http, zip_url, dataset_dir / output_filename, encoding="latin-1"
        )
        log.info(f"Saved as: {output_filename}")


def get_items_to_fetch(existing_files, response_data):
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

        # Use a "v3" prefix because this is the third variant of prescribing data
        # published. If we decide to import more historical data we'll need to
        # distinguish the different formats.
        filename = f"prescribing_{date}_v3_{published_at:%Y-%m-%dT%H%M}.parquet"

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


def remote_zipped_csv_to_parquet(http, zip_url, output_filename, **parquet_kwargs):
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp_dir = Path(tmp_name)
        zip_path = tmp_dir / "file.zip"
        csv_path = tmp_dir / "file.csv"

        http.download_to_file(zip_url, zip_path)
        extract_file_from_zip_archive(
            zip_path,
            csv_path,
            condition=lambda zipinfo: zipinfo.filename.lower().endswith(".csv"),
        )

        # Convert extracted CSV to Parquet
        output_filename.parent.mkdir(parents=True, exist_ok=True)
        parquet_tmp = get_temp_filename_for(output_filename)
        csv_to_parquet(csv_path, parquet_tmp, **parquet_kwargs)
        parquet_tmp.replace(output_filename)
