import functools
from collections import defaultdict

from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix

from .query_utils import get_dates, get_grouped_sum_ndarray, get_index_tuple


__all__ = ["get_medication_date_matrix"]


# The grouped results returned here have one row per matching BNF code (at most ~33k) so
# caching the most recently used 128 mirrors the practice matrix cache.
MEDICATION_DATE_MATRIX_CACHE_SIZE = 128


@functools.lru_cache(maxsize=MEDICATION_DATE_MATRIX_CACHE_SIZE)
def get_medication_date_matrix(cursor, query, date_count=None):
    """
    Given a `BNFQuery`, sum the prescribed items for each medication and date and return
    a `LabelledMatrix` of these values, where the rows are labelled with BNF codes and
    the columns are labelled with dates.

    The `date_count` argument allows restricting to just the N most recent months of
    prescribing data.

    There is one row for each BNF code matching the query that has prescribing in the
    date range; codes with no prescribing in the date range are omitted.

    We first build a matrix with one row per presentation (using `presentation_id`
    directly as the row index, just as `get_practice_date_matrix` uses `practice_id`)
    and then collapse it to one row per BNF code with `group_rows`.  This is necessary
    because a single BNF code can appear multiple times in the presentations table.
    """

    presentation_ids, dates = get_presentation_ids_and_dates(cursor, date_count)

    values = get_grouped_sum_ndarray(
        cursor,
        row_count=len(presentation_ids),
        col_count=len(dates),
        # `presentation_id` is a signed INT4 but `get_grouped_sum_ndarray` requires the
        # row index to be an unsigned integer type, so we cast it.
        sql=f"""
        SELECT
            CAST(presentation_id AS UINTEGER) AS row_index,
            date_id AS column_index,
            value
        FROM ({query.to_sql()})
        """,
    )

    presentation_date_matrix = LabelledMatrix(
        values,
        row_labels=presentation_ids,
        col_labels=dates,
    )

    # Collapse presentations into one row per matching BNF code.
    code_to_ids = get_bnf_code_to_presentation_ids(cursor)
    row_label_map = tuple(
        (code, code_to_ids.get(code, ()))
        for code in query.get_matching_presentation_codes()
    )
    grouped = presentation_date_matrix.group_rows(row_label_map)

    # Drop codes with no prescribing in the date range.
    return grouped.drop_zero_rows()


@functools.cache
def get_presentation_ids_and_dates(cursor, date_count):
    """
    Find the N most recent dates for which we have prescribing data and return them as an
    "index tuple" i.e. a tuple where `dates[date_id]` gives you the date with that ID.

    Also return an identity index tuple of presentation IDs (so `presentation_ids[id]`
    gives you back `id`), whose length determines the row count of the presentation-level
    matrix.
    """
    dates = get_dates(cursor, date_count)
    results = cursor.execute("SELECT id, id FROM presentation")
    presentation_ids = get_index_tuple(results.fetchall())
    return presentation_ids, dates


@functools.cache
def get_bnf_code_to_presentation_ids(cursor):
    """
    Return a dict mapping each BNF code to the tuple of presentation IDs which have that
    code.
    """
    results = cursor.execute("SELECT id, bnf_code FROM presentation")
    code_to_ids = defaultdict(list)
    for presentation_id, bnf_code in results.fetchall():
        code_to_ids[bnf_code].append(presentation_id)
    return {code: tuple(ids) for code, ids in code_to_ids.items()}
