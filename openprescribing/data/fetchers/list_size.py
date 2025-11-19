import datetime
import logging

from openprescribing.data.utils.filename_utils import get_latest_files_by_date
from openprescribing.data.utils.html_utils import (
    find_url,
    parse_nhsd_callout_boxes,
)
from openprescribing.data.utils.http_session import HTTPSession
from openprescribing.data.utils.remote_csv_utils import (
    remote_csv_to_parquet,
    remote_zipped_csv_to_parquet,
)


log = logging.getLogger(__name__)


def fetch(directory):
    dataset_dir = directory / "list_size"
    existing_files = dataset_dir.glob("*")

    http = HTTPSession("https://digital.nhs.uk", log=log.debug)
    response = http.get(
        "/data-and-information/publications/statistical/patients-registered-at-a-gp-practice/"
    )
    resources = parse_nhsd_callout_boxes(
        response.content,
        "Registered at a GP Practice",
    )
    items_to_fetch = get_items_to_fetch(existing_files, resources)

    # Any requests we now make will be to fetch new files so we log at INFO level
    http.log = log.info

    for url, output_filename in items_to_fetch:
        item_response = http.get(url)
        file_url = find_url(
            item_response.content,
            # NHS-D have an exciting variety of names for this file
            r"gp-reg-pat-prac-quin-age\.zip$",
            r"gp-reg-pat(ients)?-prac-quin-age\.csv$",
            r"gp-reg-pat-prac-quin-age[\w\-]*\.csv$",
            r"gp-reg-patients[\d\-]*\.csv$",
            r"gp_practice_counts\.csv$",
        )

        if file_url.endswith(".zip"):
            remote_zipped_csv_to_parquet(
                http, file_url, dataset_dir / output_filename, encoding="latin-1"
            )
        elif file_url.endswith(".csv"):
            remote_csv_to_parquet(
                http, file_url, dataset_dir / output_filename, encoding="latin-1"
            )
        else:
            assert False, f"Unhandled: {file_url}"

        log.info(f"Saved as: {output_filename}")


def get_items_to_fetch(existing_files, resources):
    files_by_date = get_latest_files_by_date(existing_files)

    # This is the date on which NHS-D switched to a new publication format
    new_format_start_date = datetime.date(2017, 4, 1)
    to_fetch = []
    already_fetched = 0
    total = 0
    for item in sorted(resources, key=lambda i: i.date):
        version = 2 if item.published_date >= new_format_start_date else 1
        filename = f"list_size_{item.date}_v{version}_{item.published_date}.parquet"

        if item.date in files_by_date and files_by_date[item.date].name >= filename:
            already_fetched += 1
        else:
            to_fetch.append((item.url, filename))

        total += 1

    # Use INFO where there are new files to fetch, DEBUG otherwise
    (log.info if to_fetch else log.debug)(
        f"Found {total} files: {already_fetched} already fetched and "
        f"{len(to_fetch)} to fetch"
    )

    return to_fetch
