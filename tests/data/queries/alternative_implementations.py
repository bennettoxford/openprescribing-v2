from collections import defaultdict
from itertools import product

import numpy as np

from openprescribing.data.bnf_query import BNFQuery, ProductType
from openprescribing.data.models import Org, OrgRelation
from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix


def get_practice_date_matrix_alternative(sample_data, query, date_count=None):
    practice_ids = get_practice_ids(sample_data)
    dates = get_dates(sample_data, date_count)

    if isinstance(query, BNFQuery):
        values = query_practice_prescribing_data(query, sample_data)
    else:
        values = query_practice_list_size_data(sample_data)

    values_arr = np.array(
        [
            [values[(practice_id, date)] for date in dates]
            for practice_id in practice_ids
        ]
    )
    return LabelledMatrix(values_arr, row_labels=practice_ids, col_labels=dates)


def get_org_date_ratio_matrix_alternative(sample_data, analysis):
    """Alternative implementation of get_org_date_ratio_matrix.

    Assumes that the analysis is for ICBs.  We can assert on this once org_type is added
    to Analysis.
    """

    icb_ids = get_org_ids(sample_data, Org.OrgType.ICB)
    dates = get_dates(sample_data)
    keys = list(product(icb_ids, dates))

    ntr_values = query_org_prescribing_data(
        analysis.ntr_query, Org.OrgType.ICB, sample_data
    )

    if isinstance(analysis.dtr_query, BNFQuery):
        multiplier = 100
        dtr_values = query_org_prescribing_data(
            analysis.dtr_query, Org.OrgType.ICB, sample_data
        )
    else:
        multiplier = 1000
        dtr_values = query_org_list_size_data(Org.OrgType.ICB, sample_data)

    values = {k: multiplier * ntr_values[k] / dtr_values[k] for k in keys}
    values_arr = np.array(
        [[values[(icb, date)] for date in dates] for icb in icb_ids],
    )
    return LabelledMatrix(values_arr, row_labels=icb_ids, col_labels=dates)


def query_practice_prescribing_data(query, sample_data):
    """Return dict mapping (practice_id, date) pairs to sum of items matching query that
    were prescribed by each practice on each date.
    """

    # We're not interested in testing complicated BNFQuery objects; those are adequately
    # tested in test_bnf_query.py.
    assert len(query.bnf_codes) == 1
    assert len(query.bnf_codes_excluded) == 0
    code = query.bnf_codes[0]
    assert "_" not in code
    assert query.product_type == ProductType.ALL

    values = defaultdict(int)
    for record in sample_data["prescribing_data"]:
        bnf_code = record["bnf_code"]
        if not bnf_code.startswith(code):
            continue
        key = (record["practice_code"], record["date"])
        values[key] += record["items"]
    return values


def query_practice_list_size_data(sample_data):
    """Return dict mapping (practice_id, date) pairs to the number of patients in each
    practice on each date.
    """

    values = defaultdict(int)
    for record in sample_data["list_size_data"]:
        values[(record["practice_code"], record["date"])] = record["total"]
    return values


def query_org_prescribing_data(query, org_type, sample_data):
    """Return dict mapping (org_id, date) pairs to the sum of items matching query
    prescribed by each org on each date.
    """

    practice_values = query_practice_prescribing_data(query, sample_data)
    return aggregate_by_org(practice_values, org_type)


def query_org_list_size_data(org_type, sample_data):
    """Return dict mapping (org_id, date) pairs to the number of patients in practices in
    each org on each date.
    """

    practice_values = query_practice_list_size_data(sample_data)
    return aggregate_by_org(practice_values, org_type)


def aggregate_by_org(practice_values, org_type):
    """Return dict mapping (org_id, date) to the sum of values for practices in each org
    on each date."""

    org_values = defaultdict(int)
    for (practice_id, date), value in practice_values.items():
        org_id = get_org_id(org_type, practice_id)
        org_values[(org_id, date)] += value
    return org_values


def get_dates(sample_data, date_count=None):
    """Return sorted tuple of dates that have records in the sample data."""

    dates = {r["date"] for r in sample_data["prescribing_data"]} | {
        r["date"] for r in sample_data["list_size_data"]
    }
    sorted_dates = sorted(dates, reverse=True)
    if date_count is None:
        return tuple(sorted_dates)
    else:
        return tuple(sorted_dates[:date_count])


def get_practice_ids(sample_data):
    practice_ids = {r["practice_code"] for r in sample_data["prescribing_data"]} | {
        r["practice_code"] for r in sample_data["list_size_data"]
    }
    return tuple(sorted(practice_ids))


def get_org_ids(sample_data, org_type):
    """Return sorted tuple of ids of orgs with practices that have records in the sample
    data."""

    practice_ids = {r["practice_code"] for r in sample_data["prescribing_data"]} | {
        r["practice_code"] for r in sample_data["list_size_data"]
    }
    return tuple(
        sorted(set(get_org_id(org_type, practice_id) for practice_id in practice_ids))
    )


def get_org_id(org_type, practice_id):
    """Return id of org of given type that given practice belongs to."""

    return OrgRelation.objects.get(
        child_id=practice_id, parent__org_type=org_type
    ).parent_id
