import csv

import duckdb

from openprescribing.data.ingestors import prescribing
from tests.utils.parquet_utils import parquet_from_dicts


def test_prescribing_ingest(tmp_path, settings):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"
    settings.PRESCRIBING_DATABASE = tmp_path / "data" / "prescribing.duckdb"

    test_data = generate_prescribing_data()
    write_as_parquet_files(test_data, settings.DOWNLOAD_DIR)

    prescribing.ingest()

    tables = get_all_tables(settings.PRESCRIBING_DATABASE)

    # TODO: `calculate_expected_tables` should re-implement the ingestion logic in
    # extremely boring and easy to understand Python. Once we do that we can check that
    # we get the same results from our super-efficient DuckDB SQL.
    # expected_tables = calculate_expected_tables(test_data)
    # assert tables == expected_tables

    # For now we just assert that we have the tables/views we are expecting and that
    # they are non-empty
    assert tables.keys() == {
        "date",
        "practice",
        "presentation",
        "prescribing_norm",
        "prescribing",
        "list_size_norm",
        "list_size",
        "ingested_file",
    }
    for name, table in tables.items():
        assert len(table) > 0, f"table '{name}' is empty"

    # Assert that running the ingest again with the same data doesn't rebuild the
    # database file
    last_modified = settings.PRESCRIBING_DATABASE.stat().st_mtime
    prescribing.ingest()
    assert settings.PRESCRIBING_DATABASE.stat().st_mtime == last_modified


def test_prescribing_ingest_applies_bnf_code_changes(tmp_path, settings):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"
    settings.PRESCRIBING_DATABASE = tmp_path / "data" / "prescribing.duckdb"
    settings.BNF_CODE_CHANGES_DIR = tmp_path

    test_data = {
        ("prescribing", "2023-01-01", "v3"): [
            {
                "BNF_CODE": "OLD12345",
                "SNOMED_CODE": "12345678",
                "PRACTICE_CODE": "ABC123",
                "QUANTITY": "10.0",
                "ITEMS": "100",
                "TOTAL_QUANTITY": "150.0",
                "NIC": "12.34",
                "ACTUAL_COST": "15.34",
            },
        ],
        ("prescribing", "2024-01-01", "v3"): [
            {
                "BNF_CODE": "NEW12345",
                "SNOMED_CODE": "12345678",
                "PRACTICE_CODE": "ABC123",
                "QUANTITY": "12.0",
                "ITEMS": "110",
                "TOTAL_QUANTITY": "160.0",
                "NIC": "14.34",
                "ACTUAL_COST": "17.34",
            },
        ],
        ("prescribing", "2025-01-01", "v3"): [
            {
                "BNF_CODE": "01234ABC",
                "SNOMED_CODE": "87654321",
                "PRACTICE_CODE": "ABC123",
                "QUANTITY": "12.0",
                "ITEMS": "110",
                "TOTAL_QUANTITY": "160.0",
                "NIC": "14.34",
                "ACTUAL_COST": "17.34",
            },
        ],
        ("list_size", "2023-01-01", "v2"): [
            {
                "ORG_CODE": "ABC123",
                "NUMBER_OF_PATIENTS": "12345",
                "ORG_TYPE": "GP",
                "SEX": "ALL",
                "AGE_GROUP_5": "ALL",
            },
        ],
    }
    write_as_parquet_files(test_data, settings.DOWNLOAD_DIR)

    with (settings.BNF_CODE_CHANGES_DIR / "bnf_code_mapping.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerows(
            [
                ["old_code", "new_code"],
                ["OLD12345", "NEW12345"],
            ]
        )

    prescribing.ingest()

    tables = get_all_tables(settings.PRESCRIBING_DATABASE)

    presentation_rows = sorted(
        tables["presentation"], key=lambda row: row["original_bnf_code"]
    )
    assert presentation_rows == [
        {
            "id": 1,
            "bnf_code": "01234ABC",
            "original_bnf_code": "01234ABC",
            "snomed_code": 87654321,
        },
        {
            "id": 2,
            "bnf_code": "NEW12345",
            "original_bnf_code": "NEW12345",
            "snomed_code": 12345678,
        },
        {
            "id": 3,
            "bnf_code": "NEW12345",
            "original_bnf_code": "OLD12345",
            "snomed_code": 12345678,
        },
    ]

    prescribing_rows = sorted(tables["prescribing"], key=lambda row: row["date"])
    assert len(prescribing_rows) == 3
    assert [r["date"].year for r in prescribing_rows] == [2023, 2024, 2025]
    assert [r["bnf_code"] for r in prescribing_rows] == [
        "NEW12345",
        "NEW12345",
        "01234ABC",
    ]


def generate_prescribing_data():
    # TODO: Randomly generate a whole load of prescribing data
    return {
        ("prescribing", "2025-01-01", "v3"): [
            {
                "BNF_CODE": "01234ABC",
                "SNOMED_CODE": "12345678",
                "PRACTICE_CODE": "ABC123",
                "QUANTITY": "10.0",
                "ITEMS": "100",
                "TOTAL_QUANTITY": "150.0",
                "NIC": "12.34",
                "ACTUAL_COST": "15.34",
            },
        ],
        ("prescribing", "2020-01-01", "v2"): [
            {
                "BNF_CODE": "01234ABC",
                "PRACTICE_CODE": "ABC123",
                "QUANTITY": "10.0",
                "ITEMS": "100",
                "TOTAL_QUANTITY": "150.0",
                "NIC": "12.34",
                "ACTUAL_COST": "15.34",
            },
        ],
        ("list_size", "2020-01-01", "v2"): [
            {
                "ORG_CODE": "ABC123",
                "NUMBER_OF_PATIENTS": "12345",
                "ORG_TYPE": "GP",
                "SEX": "ALL",
                "AGE_GROUP_5": "ALL",
            },
        ],
    }


def write_as_parquet_files(data, directory):
    for (source, date, version), rows in data.items():
        parquet_from_dicts(
            directory / source / f"{source}_{date}_{version}_foobar.parquet",
            rows,
        )


def get_all_tables(duckdb_path):
    conn = duckdb.connect(duckdb_path)
    return {
        name: fetch_table_as_dicts(conn, name) for name in list_tables_and_views(conn)
    }


def fetch_table_as_dicts(conn, name):
    cursor = conn.execute(f"SELECT * FROM {name}")
    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def list_tables_and_views(conn):
    cursor = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    )
    return [r[0] for r in cursor.fetchall()]
