import textwrap

import duckdb
import pytest
import responses

from openprescribing.data.fetchers import drug_tariff


@pytest.mark.parametrize(
    "link_url, csv_url, date",
    [
        (
            "https://www.nhsbsa.nhs.uk/sites/default/files/2025-10/Part%20VIIIA%20Apr%2026.xls.csv",
            "https://www.nhsbsa.nhs.uk/sites/default/files/2025-10/Part%20VIIIA%20Apr%2026.xls.csv",
            "2026-04",
        ),
        (
            "https://www.nhsbsa.nhs.uk/sites/default/files/2025-10/Part%20VIIIA%20Nov%2020%20updated.csv",
            "https://www.nhsbsa.nhs.uk/sites/default/files/2025-10/Part%20VIIIA%20Nov%2020%20updated.csv",
            "2020-11",
        ),
        (
            "https://www.nhsbsa.nhs.uk/sites/default/files/2025-12/Part%20VIIIA%20December%2020251.xls_0.csv",
            "https://www.nhsbsa.nhs.uk/sites/default/files/2025-12/Part%20VIIIA%20December%2020251.xls.csv",
            "2025-12",
        ),
    ],
)
@responses.activate
def test_fetch_drug_tariff(tmp_path, link_url, csv_url, date):
    responses.get(
        "https://www.nhsbsa.nhs.uk/pharmacies-gp-practices-and-appliance-contractors/drug-tariff/drug-tariff-part-viii",
        body=f'<html><a href="{link_url}">{date}</a></html>',
    )

    CSV_FILE = textwrap.dedent(
        """\
        November Drug Tariff Part VIIIA,,,,,,
        ,,,,,,
        Medicine,Pack size,,VMP Snomed Code,VMPP Snomed Code,Drug Tariff Category,Basic Price
        Abacavir 600mg / Lamivudine 300mg tablets,30,tablet,39724011000001106,8991611000001104,Part VIIIA Category C,35225
        Abatacept 125mg/1ml solution for injection pre-filled disposable devices,4,pre-filled disposable injection,29767011000001106,29747011000001102,Part VIIIA Category C,120960
        Acamprosate 333mg gastro-resistant tablets,168,tablet,42267511000001104,994511000001109,Part VIIIA Category M,2172
        """
    )
    responses.get(
        csv_url,
        body=CSV_FILE,
    )

    drug_tariff.fetch(tmp_path)

    path = tmp_path / "drug_tariff" / f"drug_tariff_{date}-01.parquet"
    results = duckdb.read_parquet(str(path))
    assert results.columns == [
        "Medicine",
        "Pack size",
        "column2",
        "VMP Snomed Code",
        "VMPP Snomed Code",
        "Drug Tariff Category",
        "Basic Price",
    ]
    assert results.fetchall() == [
        (
            "Abacavir 600mg / Lamivudine 300mg tablets",
            "30",
            "tablet",
            "39724011000001106",
            "8991611000001104",
            "Part VIIIA Category C",
            "35225",
        ),
        (
            "Abatacept 125mg/1ml solution for injection pre-filled disposable devices",
            "4",
            "pre-filled disposable injection",
            "29767011000001106",
            "29747011000001102",
            "Part VIIIA Category C",
            "120960",
        ),
        (
            "Acamprosate 333mg gastro-resistant tablets",
            "168",
            "tablet",
            "42267511000001104",
            "994511000001109",
            "Part VIIIA Category M",
            "2172",
        ),
    ]


@responses.activate
def test_fetch_drug_tariff_already_fetched(tmp_path):
    csv_url = "https://www.nhsbsa.nhs.uk/sites/default/files/2025-10/Part%20VIIIA%20Nov%2025.xls.csv"

    responses.get(
        "https://www.nhsbsa.nhs.uk/pharmacies-gp-practices-and-appliance-contractors/drug-tariff/drug-tariff-part-viii",
        body=f'<html><a href="{csv_url}">Nov 2025</a></html>',
    )

    responses.get(
        csv_url,
        body=Exception("Should not re-download this file"),
    )

    dataset_dir = tmp_path / "drug_tariff"
    dataset_dir.mkdir(exist_ok=True, parents=True)
    path = dataset_dir / "drug_tariff_2025-11-01.parquet"
    path.touch()

    drug_tariff.fetch(tmp_path)
