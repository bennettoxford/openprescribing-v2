from openprescribing.data.analysis import Analysis
from openprescribing.data.bnf_query import BNFQuery
from openprescribing.data.list_size_query import ListSizeQuery
from openprescribing.data.queries import get_org_date_ratio_matrix
from tests.utils.rxdb_utils import assert_approx_equal

from .alternative_implementations import get_org_date_ratio_matrix_alternative


def test_get_org_date_ratio_matrix_prescribing_vs_list_size(rxdb, sample_data):
    analysis = Analysis(
        ntr_query=BNFQuery(bnf_codes=["1001030U0AAABAB"]),
        dtr_query=ListSizeQuery(),
        org_id="ICB01",
    )

    with rxdb.get_cursor() as cursor:
        odm = get_org_date_ratio_matrix(cursor, analysis)

    expected_odm = get_org_date_ratio_matrix_alternative(sample_data, analysis)

    assert_approx_equal(odm, expected_odm)


def test_get_org_date_ratio_matrix_prescribing_vs_prescribing(rxdb, sample_data):
    analysis = Analysis(
        ntr_query=BNFQuery(bnf_codes=["1001030U0AAABAB"]),
        dtr_query=BNFQuery(bnf_codes=["1001030U0"]),
        org_id="ICB01",
    )

    with rxdb.get_cursor() as cursor:
        odm = get_org_date_ratio_matrix(cursor, analysis)

    expected_odm = get_org_date_ratio_matrix_alternative(sample_data, analysis)

    assert_approx_equal(odm, expected_odm)
