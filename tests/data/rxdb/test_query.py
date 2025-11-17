from datetime import date

from openprescribing.data.rxdb import get_practice_date_matrix


def test_get_practice_date_matrix(rxdb):
    # TODO: This is really not a great test, but it does exercise the full logic and
    # demonstrate the basic process.
    rxdb.ingest(
        [
            {"date": "2025-01-01", "practice_code": "JKL123", "items": 90},
            {"date": "2025-02-01", "practice_code": "ABC123", "items": 25},
            {"date": "2025-02-01", "practice_code": "GHI123", "items": 40},
            {"date": "2025-03-01", "practice_code": "ABC123", "items": 10},
            {"date": "2025-03-01", "practice_code": "DEF123", "items": 30},
            {"date": "2025-03-01", "practice_code": "GHI123", "items": 15},
        ],
    )

    with rxdb.get_cursor() as cursor:
        matrix = get_practice_date_matrix(
            cursor,
            "SELECT practice_id, date_id, items AS value FROM prescribing",
            date_count=2,
        )

    assert matrix.row_labels == ("ABC123", "DEF123", "GHI123")
    assert matrix.col_labels == (date(2025, 3, 1), date(2025, 2, 1))

    assert matrix.values.tolist() == [
        [10, 25],
        [30, 0],
        [15, 40],
    ]
