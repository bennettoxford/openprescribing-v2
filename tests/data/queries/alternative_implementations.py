from collections import defaultdict

import numpy as np

from openprescribing.data.bnf_query import BNFQuery, ProductType
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


def query_practice_prescribing_data(query, sample_data):
    """Return dict mapping (practice_id, date) pairs to sum of items matching query that
    were prescribed by each practice on each date.
    """

    # We're not interested in testing complicated BNFQuery objects; those are adequately
    # tested in test_bnf_query.py.
    assert len(query.terms) == 1
    assert not query.terms[0].negated
    code = query.terms[0].code
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
    """Return IDs of practices that have records in the same data."""
    practice_ids = {r["practice_code"] for r in sample_data["prescribing_data"]} | {
        r["practice_code"] for r in sample_data["list_size_data"]
    }
    return tuple(sorted(practice_ids))
