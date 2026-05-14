import pytest

from openprescribing.data.ingestors import drug_tariff
from openprescribing.data.models import TariffPrice
from tests.utils.parquet_utils import parquet_from_dicts


@pytest.mark.django_db(databases=["data"])
def test_tariff_ingest(tmp_path, settings):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"

    data = [
        {
            "Medicine": "Idebenone 150mg tablets",
            "VMPP Snomed Code": "31461411000001100",
            "Drug Tariff Category": "Part VIIIA Category C",
            "Basic Price": "636400",
        },
    ]

    drug_tariff_file = (
        settings.DOWNLOAD_DIR / "drug_tariff" / "drug_tariff_2026-04-01.parquet"
    )
    parquet_from_dicts(drug_tariff_file, data)

    # Ingests data for 2026-04-01
    drug_tariff.ingest()

    results = [
        (
            tariff_price.vmpp_id,
            str(tariff_price.date),
            tariff_price.drug_tariff_category_id,
            tariff_price.price_in_pence,
        )
        for tariff_price in TariffPrice.objects.all()
    ]
    assert results == [
        (31461411000001100, "2026-04-01", 3, 636400),
    ]

    data = [
        {
            "Medicine": "Idebenone 150mg tablets",
            "VMPP Snomed Code": "31461411000001100",
            "Drug Tariff Category": "Part VIIIA Category C",
            "Basic Price": "636401",
        },
    ]

    drug_tariff_file = (
        settings.DOWNLOAD_DIR / "drug_tariff" / "drug_tariff_2026-05-01.parquet"
    )
    parquet_from_dicts(drug_tariff_file, data)

    # Skips ingesting 2026-04-01 and just ingests 2026-05-01
    drug_tariff.ingest()

    results = [
        (
            tariff_price.vmpp_id,
            str(tariff_price.date),
            tariff_price.drug_tariff_category_id,
            tariff_price.price_in_pence,
        )
        for tariff_price in TariffPrice.objects.all()
    ]
    assert results == [
        (31461411000001100, "2026-04-01", 3, 636400),
        (31461411000001100, "2026-05-01", 3, 636401),
    ]

    # Attempting to re-ingest the same named file should do nothing. As a simple check for
    # this we empty the file contents and re-ingest. If the code does attempt to load it
    # then this will fail loudly.
    drug_tariff_file.write_text("")
    drug_tariff.ingest()


@pytest.mark.django_db(databases=["data"])
def test_ods_ingest_missing_price(tmp_path, settings):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"

    data = [
        {
            "Medicine": "Idebenone 150mg tablets",
            "VMPP Snomed Code": "31461411000001100",
            "Drug Tariff Category": "Part VIIIA Category C",
            "Basic Price": None,
        },
    ]

    drug_tariff_file = (
        settings.DOWNLOAD_DIR / "drug_tariff" / "drug_tariff_2025-09-01.parquet"
    )
    parquet_from_dicts(drug_tariff_file, data)

    drug_tariff.ingest()

    results = [
        (
            tariff_price.vmpp_id,
            str(tariff_price.date),
            tariff_price.drug_tariff_category_id,
            tariff_price.price_in_pence,
        )
        for tariff_price in TariffPrice.objects.all()
    ]
    assert results == []
