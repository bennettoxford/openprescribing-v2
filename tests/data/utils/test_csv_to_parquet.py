import csv

import duckdb

from openprescribing.data.utils.csv_to_parquet import csv_to_parquet


def test_csv_to_parquet(tmp_path):
    input_data = [
        {
            # Character encoding should be handled correctly
            "text_column": "with “smart” quotes",
            # Numbers should be left as text and not converted
            "numeric_column": "123",
        },
        {
            # Escaping should be handled correctly
            "text_column": "new\nline\n,",
            # NULLs are handled correctly
            "numeric_column": None,
        },
    ]
    input_file = tmp_path / "input.csv"
    with input_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, input_data[0].keys())
        writer.writeheader()
        writer.writerows(input_data)

    output_file = tmp_path / "output.parquet"
    csv_to_parquet(input_file, output_file)

    results = duckdb.read_parquet(str(output_file))
    result_dicts = [dict(zip(results.columns, row)) for row in results.fetchall()]
    assert result_dicts == input_data
