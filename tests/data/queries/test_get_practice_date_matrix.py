from datetime import date

import pytest

from openprescribing.data.bnf_query import BNFQuery
from openprescribing.data.list_size_query import ListSizeQuery
from openprescribing.data.models import BNFCode
from openprescribing.data.queries import get_practice_date_matrix


@pytest.mark.django_db(databases=["data"])
def test_get_practice_date_matrix(rxdb):
    # TODO: This is really not a great test, but it does exercise the full logic and
    # demonstrate the basic process.
    BNFCode.objects.create(code="1001030U0AAABAB", level=7)
    rxdb.ingest(
        [
            {
                # not included: too early
                "date": "2025-01-01",
                "practice_code": "JKL123",
                "bnf_code": "1001030U0AAABAB",
                "items": 90,
            },
            {
                # not included: wrong code
                "date": "2025-02-01",
                "practice_code": "ABC123",
                "bnf_code": "0601060D0BSAAA0",
                "items": 25,
            },
            {
                "date": "2025-02-01",
                "practice_code": "ABC123",
                "bnf_code": "1001030U0AAABAB",
                "items": 25,
            },
            {
                "date": "2025-02-01",
                "practice_code": "ABC123",
                "bnf_code": "1001030U0AAABAB",
                "items": 15,
            },
            {
                "date": "2025-02-01",
                "practice_code": "GHI123",
                "bnf_code": "1001030U0AAABAB",
                "items": 40,
            },
            {
                "date": "2025-03-01",
                "practice_code": "ABC123",
                "bnf_code": "1001030U0AAABAB",
                "items": 10,
            },
            {
                "date": "2025-03-01",
                "practice_code": "DEF123",
                "bnf_code": "1001030U0AAABAB",
                "items": 30,
            },
            {
                "date": "2025-03-01",
                "practice_code": "GHI123",
                "bnf_code": "1001030U0AAABAB",
                "items": 15,
            },
        ],
    )

    query = BNFQuery.build(["1001030U0AAABAB"], "all")

    with rxdb.get_cursor() as cursor:
        matrix = get_practice_date_matrix(cursor, query, date_count=2)

    assert matrix.row_labels == ("ABC123", "DEF123", "GHI123")
    assert matrix.col_labels == (date(2025, 3, 1), date(2025, 2, 1))

    assert matrix.values.tolist() == [
        [10, 40],
        [30, 0],
        [15, 40],
    ]


def test_get_practice_date_matrix_for_list_sizes(rxdb):
    rxdb.ingest(
        [
            {"date": "2025-03-01", "practice_code": "ABC123"},
            {"date": "2025-02-01", "practice_code": "DEF123"},
            {"date": "2025-01-01", "practice_code": "GHI123"},
        ],
        list_size_data=[
            {"date": "2025-01-01", "practice_code": "ABC123", "total": 10},
            {"date": "2025-02-01", "practice_code": "DEF123", "total": 20},
            {"date": "2025-03-01", "practice_code": "GHI123", "total": 30},
        ],
    )

    with rxdb.get_cursor() as cursor:
        matrix = get_practice_date_matrix(cursor, ListSizeQuery())

    assert matrix.row_labels == ("ABC123", "DEF123", "GHI123")
    assert matrix.col_labels == (date(2025, 3, 1), date(2025, 2, 1), date(2025, 1, 1))

    assert matrix.values.tolist() == [
        [0, 0, 10],
        [0, 20, 0],
        [30, 0, 0],
    ]
