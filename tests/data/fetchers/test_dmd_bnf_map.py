import csv
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import duckdb
import responses
from openpyxl import Workbook

from openprescribing.data.fetchers import dmd_bnf_map


@responses.activate
def test_dmd_bnf_map_fetch(tmp_path):
    body = """
    <a href="/sites/default/files/2026-03/BNF%20Snomed%20Mapping%20data%2020260324.zip">SNOMED - BNF mapping document January 2026 (ZIP file: 18.3MB)</a>
    <a href="/sites/default/files/2026-02/BNF%20Snomed%20Mapping%20data%2020260216.zip">December 2025 (ZIP file: 18.8MB)</a>
    <a href="/sites/default/files/2026-01/BNF%20Snomed%20Mapping%20Data%2020260120.zip">November 2025 (ZIP file: 18.3MB)</a>
    """
    responses.get(
        "https://www.nhsbsa.nhs.uk/prescription-data/understanding-our-data/bnf-snomed-mapping",
        body=body,
    )

    responses.get(
        "https://www.nhsbsa.nhs.uk/sites/default/files/2026-03/BNF%20Snomed%20Mapping%20data%2020260324.zip",
        body=create_zipped_xlsx_from_csv(Path("tests/fixtures/dmd_bnf_map.csv")),
    )

    dmd_bnf_map.fetch(tmp_path)

    map_file = tmp_path / "dmd_bnf_map" / "dmd_bnf_map_2026-01-01_2026-03-24.parquet"
    results = duckdb.read_parquet(str(map_file))
    assert results.columns == ["SNOMED Code", "BNF Code"]
    assert len(results) == 19
    assert results.fetchone() == ("3549611000001100", "0914011B0AAAAAA")


@responses.activate
def test_dmd_bnf_map_fetch_when_alread_fetched(tmp_path):
    body = """
    <a href="/sites/default/files/2026-03/BNF%20Snomed%20Mapping%20data%2020260324.zip">SNOMED - BNF mapping document January 2026 (ZIP file: 18.3MB)</a>
    """
    responses.get(
        "https://www.nhsbsa.nhs.uk/prescription-data/understanding-our-data/bnf-snomed-mapping",
        body=body,
    )

    (tmp_path / "dmd_bnf_map").mkdir()
    (tmp_path / "dmd_bnf_map" / "dmd_bnf_map_2026-01-01_2026-03-24.parquet").touch()

    dmd_bnf_map.fetch(tmp_path)

    assert not any(
        call.request.url
        == "https://www.nhsbsa.nhs.uk/sites/default/files/2026-03/BNF%20Snomed%20Mapping%20data%2020260324.zip"
        for call in responses.calls
    )


def create_zipped_xlsx_from_csv(csv_path):
    wb = Workbook()
    ws = wb.active

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            ws.append(row)

    xlsx_buffer = BytesIO()
    wb.save(xlsx_buffer)
    xlsx_buffer.seek(0)

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zf:
        zf.writestr("dmd_bnf_map.xlsx", xlsx_buffer.getvalue())

    return zip_buffer.getvalue()
