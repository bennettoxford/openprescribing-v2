from openprescribing.data.models import Org

from ..bnf_query import BNFQuery
from .get_practice_date_matrix import get_practice_date_matrix


def get_org_date_ratio_matrix(cursor, analysis, date_count=None):
    """Return a matrix with one row per org and one column per date, giving ratio
    between numerator and denominator values specified by queries in given analysis."""

    ntr_pdm = get_practice_date_matrix(
        cursor, analysis.ntr_query, date_count=date_count
    )
    dtr_pdm = get_practice_date_matrix(
        cursor, analysis.dtr_query, date_count=date_count
    )

    if analysis.org_id is not None:
        org_type = Org.objects.get(id=analysis.org_id).org_type
    else:
        org_type = Org.OrgType.ICB

    org_id_to_practice_ids = Org.objects.filter(org_type=org_type).with_practice_ids()

    ntr_odm = ntr_pdm.group_rows(org_id_to_practice_ids)
    dtr_odm = dtr_pdm.group_rows(org_id_to_practice_ids)

    # For prescribing vs prescribing queries, we want to show the numerator values
    # as a percentage of the denominator values.  For prescribing vs list size
    # queries, we want to show the numerator values per thousand patients.
    multiplier = 100 if isinstance(analysis.dtr_query, BNFQuery) else 1000

    odm = ntr_odm / dtr_odm * multiplier

    return odm
