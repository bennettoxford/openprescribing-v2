from datetime import date

import pytest

from openprescribing.data.bnf_query import BNFQuery
from openprescribing.data.list_size_query import ListSizeQuery
from openprescribing.data.models import BNFCode
from openprescribing.data.queries import get_practice_date_matrix
from tests.utils.rxdb_utils import assert_approx_equal

from .alternative_implementations import get_practice_date_matrix_alternative


@pytest.mark.django_db(databases=["data"])
def test_get_practice_date_matrix_spot_check(rxdb):
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
        pdm = get_practice_date_matrix(cursor, query, date_count=2)

    assert pdm.row_labels == ("ABC123", "DEF123", "GHI123")
    assert pdm.col_labels == (date(2025, 3, 1), date(2025, 2, 1))

    assert pdm.values.tolist() == [
        [10, 40],
        [30, 0],
        [15, 40],
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_practice_date_matrix_for_bnf_query(rxdb, sample_data):
    query = BNFQuery.build(["1001030U0AAABAB"], "all")

    with rxdb.get_cursor() as cursor:
        pdm = get_practice_date_matrix(cursor, query, date_count=2)

    expected_pdm = get_practice_date_matrix_alternative(
        sample_data, query, date_count=2
    )

    assert_approx_equal(pdm, expected_pdm)


@pytest.mark.django_db(databases=["data"])
def test_get_practice_date_matrix_for_list_sizes(rxdb, sample_data):
    query = ListSizeQuery()

    with rxdb.get_cursor() as cursor:
        pdm = get_practice_date_matrix(cursor, query)

    expected_pdm = get_practice_date_matrix_alternative(sample_data, query)

    assert_approx_equal(pdm, expected_pdm)
