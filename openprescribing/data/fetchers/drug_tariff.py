import calendar
import datetime
import logging
import os
import re
from urllib.parse import unquote

from bs4 import BeautifulSoup

from openprescribing.data.utils.http_session import HTTPSession
from openprescribing.data.utils.remote_csv_utils import remote_csv_to_parquet


log = logging.getLogger(__name__)


def fetch(directory):
    """Fetch most recent Drug Tariff files from
    https://www.nhsbsa.nhs.uk/pharmacies-gp-practices-and-appliance-contractors/drug-tariff/drug-tariff-part-viii .
    """

    dataset_dir = directory / "drug_tariff"
    dataset_dir.mkdir(exist_ok=True, parents=True)

    http = HTTPSession(
        "https://www.nhsbsa.nhs.uk/",
        # We start with DEBUG level logging while we're checking if there's anything new
        # to fetch
        log=log.debug,
    )
    rsp = http.get(
        "pharmacies-gp-practices-and-appliance-contractors/drug-tariff/drug-tariff-part-viii"
    )
    doc = BeautifulSoup(rsp.text, "html.parser")

    imported_months = []
    already_fetched = 0

    # Log CSV files as INFO level
    http.log = log.info

    for a in doc.find_all("a", href=re.compile(r"Part%20VIIIA.+\.csv$")):
        csv_url = a.attrs["href"]

        # csv_url typically has a filename part like Part%20VIIIA%20September%202017.csv
        base_filename = unquote(os.path.splitext(os.path.basename(csv_url))[0])

        year, month = convert_base_filename_to_year_and_month(base_filename)
        date = datetime.date(int(year), month, 1)
        release_id = f"drug_tariff_{date}"
        release_path = dataset_dir / f"{release_id}.parquet"

        if release_path.exists():
            log.debug(f"Already fetched a file for this release: {release_id}")
            already_fetched += 1
            continue

        # Fix broken link
        csv_url = csv_url.replace(
            "Part%20VIIIA%20December%2020251.xls_0.csv",
            "Part%20VIIIA%20December%2020251.xls.csv",
        )

        remote_csv_to_parquet(
            http, csv_url, dataset_dir / release_path, encoding="latin-1", skip=2
        )

        imported_months.append((year, month))

    newly_fetched = len(imported_months)
    total = already_fetched + newly_fetched

    (log.info if imported_months else log.debug)(
        f"Found {total} files: {already_fetched} already fetched and "
        f"{newly_fetched} newly fetched"
    )


def convert_base_filename_to_year_and_month(base_filename):
    month_abbrs = [x.lower() for x in calendar.month_abbr]

    if base_filename == "Part VIIIA Nov 20 updated":
        # November 2020 has a different filename.  In general we want to be
        # warned (through the scraper crashing) about updates (because we have
        # to delete all records for the month in question, and reimport) so
        # special-casing is appropriate here.
        year, month = "2020", 11

    else:
        # Split the filename into e.g. ['Part', 'VIIIA', 'September', '2017']
        words = re.split(r"[ -]+", base_filename)
        month_name, year = words[-2:]

        # We have seen the last token in `words` be "19_0".  The year is
        # reported to us via Slack, so if we pull out some nonsense here we
        # *should* notice.
        year = re.match(r"\d+", year).group()

        # Fix typo
        if year == "20251":
            year = "2025"

        if len(year) == 2:
            year = "20" + year

        # We have seen the month be `September`, `Sept`, and `Sep`.
        month_abbr = month_name.lower()[:3]
        month = month_abbrs.index(month_abbr)

    return year, month
