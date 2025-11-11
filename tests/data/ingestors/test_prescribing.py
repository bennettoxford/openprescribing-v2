import duckdb
import pyarrow
import pyarrow.parquet

from openprescribing.data.ingestors import prescribing


def test_prescribing_ingest(tmp_path, settings):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"
    settings.DATA_DIR = tmp_path / "data"

    test_data = generate_prescribing_data()
    write_as_parquet_files(test_data, settings.DOWNLOAD_DIR / "prescribing")

    prescribing.ingest()

    tables = get_all_tables(settings.DATA_DIR / "prescribing.duckdb")

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
    }
    for name, table in tables.items():
        assert len(table) > 0, f"table '{name}' is empty"


def generate_prescribing_data():
    # TODO: Randomly generate a whole load of prescribing data
    return {
        ("2025-01-01", "v3"): [
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
        ]
    }


def write_as_parquet_files(data, directory):
    directory.mkdir(parents=True, exist_ok=True)
    for (date, version), rows in data.items():
        filename = directory / f"prescribing_{date}_{version}_foobar.parquet"
        table = pyarrow.Table.from_pylist(rows)
        pyarrow.parquet.write_table(table, filename)


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
