import csv

from django.core.management import call_command


def test_create_bnf_code_mapping(tmp_path, settings):
    settings.BNF_CODE_CHANGES_DIR = tmp_path
    (tmp_path / "raw").mkdir()

    write_csv(tmp_path, 2024, [["A1", "A2"], ["B1", "B2"]])
    write_csv(tmp_path, 2025, [["A2", "A3"], ["C1", "C2"]])
    write_csv(tmp_path, 2026, [["A3", "A4"], ["B2", "B3"]])

    call_command("create_bnf_code_mapping")

    with (tmp_path / "bnf_code_mapping.csv").open() as f:
        mapping = {row["old_code"]: row["new_code"] for row in csv.DictReader(f)}

    assert mapping == {
        "A1": "A4",
        "A2": "A4",
        "A3": "A4",
        "B1": "B3",
        "B2": "B3",
        "C1": "C2",
    }


def write_csv(tmp_path, year, rows):
    with (tmp_path / "raw" / f"{year}.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
