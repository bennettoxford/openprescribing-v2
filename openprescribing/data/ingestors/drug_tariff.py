import datetime
import logging
import re

import duckdb
from django.conf import settings

from openprescribing.data.models import IngestedFile, TariffPrice
from openprescribing.data.utils.duckdb_utils import escape


log = logging.getLogger(__name__)


def ingest(force=False):
    drug_tariff_files = sorted(settings.DOWNLOAD_DIR.glob("drug_tariff/*"))

    latest_file = drug_tariff_files[-1]

    if not force and (
        not latest_file
        or str(drug_tariff_file_date(latest_file))
        <= IngestedFile.get_by_name("drug_tariff")
    ):
        log.debug("No new Drug Tariff data found to ingest")
        return

    conn = duckdb.connect()

    for drug_tariff_file in drug_tariff_files:
        date = drug_tariff_file_date(drug_tariff_file)

        if not force and (str(date) <= IngestedFile.get_by_name("drug_tariff")):
            log.debug(f"Skipping Drug Tariff ingest for {date}")
            continue

        log.debug(f"Starting Drug Tariff ingest for {date}")
        TariffPrice.objects.filter(date=date).delete()

        query = f'SELECT "Medicine", "VMPP Snomed Code", "Drug Tariff Category", "Basic Price" FROM read_parquet({escape(drug_tariff_file)})'

        results = conn.sql(query)
        for (
            medicine,
            vmpp_snomed_code,
            drug_tariff_category,
            basic_price,
        ) in results.fetchall():
            if not basic_price:
                log.info(
                    f"Missing price for {medicine} / {vmpp_snomed_code} Drug Tariff for {date}"
                )
                continue

            TariffPrice.objects.create(
                date=date,
                vmpp_id=vmpp_snomed_code,
                drug_tariff_category_id=get_tariff_cat_id(drug_tariff_category),
                price_in_pence=int(basic_price),
            )

        log.info(f"Finished Drug Tariff ingest for {date}")
        IngestedFile.set_by_name("drug_tariff", str(date))

    log.debug("Drug Tariff ingest complete")


def drug_tariff_file_date(filename):
    match = re.match(r".*drug_tariff_(\d{4}-\d{2}-\d{2})\.parquet", str(filename))
    assert match, f"Expecting a filename containing an ISO date: {filename}"
    return datetime.date.fromisoformat(match.group(1))


def get_tariff_cat_id(cat):
    # These IDs correspond to the dmd.DtPaymentCategory model.
    category_ids = [
        ("Category A", 1),
        ("Category C", 3),
        ("Category H", 15),
        ("Category M", 11),
    ]

    for category_name, category_id in category_ids:
        if category_name in cat:
            return category_id
    assert False, f"Unknown category: {cat}"
