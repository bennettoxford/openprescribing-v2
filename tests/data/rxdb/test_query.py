from datetime import date

import duckdb

from openprescribing.data import rxdb


def test_get_practice_date_matrix():
    # TODO: This is really not a great test, but it does exercise the full logic and
    # demonstrate the basic process.
    practices = ["ABC123", "DEF123", "GHI123", "JKL123"]
    dates = [date(2025, 3, 1), date(2025, 2, 1), date(2025, 1, 1)]
    last_prescribing_dates = {"JKL123": date(2025, 1, 1)}

    conn = duckdb.connect()
    conn.sql(
        """
        CREATE TABLE date (
            id UINTEGER, date DATE
        );
        CREATE TABLE practice (
            id UINTEGER, code VARCHAR, latest_prescribing_date DATE
        );
        CREATE TABLE prescribing (
            practice_id UINTEGER, date_id UINTEGER, items INTEGER
        )
        """
    )

    conn.executemany(
        "INSERT INTO date VALUES(?, ?)",
        enumerate(dates),
    )
    conn.executemany(
        "INSERT INTO practice VALUES(?, ?, ?)",
        [
            (
                i,
                code,
                last_prescribing_dates.get(code, dates[0]),
            )
            for i, code in enumerate(practices)
        ],
    )
    conn.executemany(
        "INSERT INTO prescribing VALUES(?, ?, ?)",
        [
            (0, 0, 10),
            (1, 0, 30),
            (2, 0, 15),
            (0, 1, 25),
            (2, 1, 40),
        ],
    )

    matrix = rxdb.get_practice_date_matrix(
        conn,
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
