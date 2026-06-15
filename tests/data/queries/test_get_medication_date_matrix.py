from datetime import date

from openprescribing.data.bnf_query import BNFQuery
from openprescribing.data.models import BNFCode
from openprescribing.data.queries import get_medication_date_matrix
from tests.utils.rxdb_utils import assert_approx_equal

from .alternative_implementations import get_medication_date_matrix_alternative


def test_get_medication_date_matrix_spot_check(rxdb):
    BNFCode.objects.create(code="1001030U0AAABAB", level=7)
    BNFCode.objects.create(code="1001030U0AAACAC", level=7)
    # Matches the query prefix but is only prescribed outside the date window, so is
    # not included in result.
    BNFCode.objects.create(code="1001030U0AAADAD", level=7)
    # Matches the query prefix but is never prescribed at all, so is not included in
    # result.
    BNFCode.objects.create(code="1001030U0AAAEAE", level=7)
    rxdb.ingest(
        [
            {
                # not included: too early
                "date": "2025-01-01",
                "practice_code": "ABC123",
                "bnf_code": "1001030U0AAABAB",
                "items": 90,
            },
            {
                # not included: too early
                "date": "2025-01-01",
                "practice_code": "ABC123",
                "bnf_code": "1001030U0AAADAD",
                "items": 50,
            },
            {
                # not included: wrong code
                "date": "2025-02-01",
                "practice_code": "ABC123",
                "bnf_code": "0601060D0BSAAA0",
                "items": 99,
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
                "date": "2025-02-01",
                "practice_code": "ABC123",
                "bnf_code": "1001030U0AAACAC",
                "items": 5,
            },
            {
                "date": "2025-03-01",
                "practice_code": "ABC123",
                "bnf_code": "1001030U0AAABAB",
                "items": 10,
            },
            {
                "date": "2025-03-01",
                "practice_code": "GHI123",
                "bnf_code": "1001030U0AAABAB",
                "items": 15,
            },
            {
                "date": "2025-03-01",
                "practice_code": "DEF123",
                "bnf_code": "1001030U0AAACAC",
                "items": 7,
            },
        ],
    )

    query = BNFQuery(bnf_codes=["1001030U0"])

    with rxdb.get_cursor() as cursor:
        mdm = get_medication_date_matrix(cursor, query, date_count=2)

    assert mdm.row_labels == (
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    )
    assert mdm.col_labels == (date(2025, 3, 1), date(2025, 2, 1))

    assert mdm.values.tolist() == [
        [25, 80],
        [7, 5],
    ]


def test_get_medication_date_matrix_for_bnf_query(rxdb, sample_data):
    query = BNFQuery(bnf_codes=["1001030U0"])

    with rxdb.get_cursor() as cursor:
        mdm = get_medication_date_matrix(cursor, query, date_count=2)

    expected_mdm = get_medication_date_matrix_alternative(
        sample_data, query, date_count=2
    )

    assert_approx_equal(mdm, expected_mdm)
