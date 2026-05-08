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

    # a list of two-tuples, (resource ID, resource filename)
    items_to_fetch = get_items_to_fetch(existing_files, response_data, version_number)

    # Any requests we now make will be to fetch new files so we log at INFO level
    http.log = log.info

    for item_id, output_filename in items_to_fetch:
        # We request a resource again because the ZIP URL expires an hour after it's
        # generated. If we didn't, and used the ZIP URLs in the original request, then
        # the more resources we fetched, the greater the likelihood of their URLs
        # expiring.
        item_resp = http.get("action/resource_show", params={"id": item_id})
        zip_url = item_resp.json()["result"]["zip_url"]
        remote_zipped_csv_to_parquet(
            http, zip_url, dataset_dir / output_filename, encoding="latin-1"
        )
        log.info(f"Saved as: {output_filename}")


def get_items_to_fetch(existing_files, response_data, version_number):
    """
    Prescribing data are published in monthly batches, three months in arrears. Whilst
    there may be multiple batches per month, later batches subsume earlier batches. We
    save batches in files named according to the following pattern:

    prescribing_<batch-date>_v<epd-version-number>_<publication-datetime>.parquet

    <batch-date>
        The date of the batch. This is always the first of the month.

    <epd-version-number>
        The version of the English Prescribing Dataset (EPD).
        Version 3 has SNOMED codes. Version 2 doesn't and is retired.

    <publication-datetime>
        The date and time the batch was published.
    """

    # for each batch-date, get the file with the latest publication-datetime
    files_by_date = get_latest_files_by_date(existing_files)
    # a resource is a published batch
    resources = response_data["result"]["resources"]

    to_fetch = []
    already_fetched = 0
    total = 0
    # We extract the batch-date from the name, so this iterates from earliest to latest
    # batch-date.
    for item in sorted(resources, key=lambda i: i["name"]):
        # extract the batch-date
        year_month = re.match(r"^EPD_(?:SNOMED_)?(\d{6})$", item["name"]).group(1)
        date = datetime.date.fromisoformat(f"{year_month}01")

        # extract the publication-datetime
        published_at = datetime.datetime.fromisoformat(
            # Oddly `last_modified` is sometimes null (maybe before the first update?)
            # so we have to use the `created` date
            item["last_modified"] or item["created"]
        )

        # the filename of the resource, if we were to save the resource to a file
        filename = (
            f"prescribing_{date}_v{version_number}_{published_at:%Y-%m-%dT%H%M}.parquet"
        )

        if date in files_by_date and files_by_date[date].name >= filename:
            # We've already fetched a batch with the batch-date and it was published at
            # the same time as or later than the resource.
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
