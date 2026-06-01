import functools

from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix

from .query_utils import get_dates, get_grouped_sum_ndarray, get_index_tuple


__all__ = ["get_practice_date_matrix"]


# The largest of these matrices are about 16MB in size (140 dates x 15,000 practices x 8
# bytes per value). Caching the most recently used 128 only takes 2GB of RAM and should
# mean we can serve common queries from the cache.
PRACTICE_DATE_MATRIX_CACHE_SIZE = 128


@functools.lru_cache(maxsize=PRACTICE_DATE_MATRIX_CACHE_SIZE)
def get_practice_date_matrix(cursor, query, date_count=None):
    """
    Given BNFQuery or ListSizeQuery, sum all the values for each practice and date and
    return a `LabelledMatrix` of these values, where the rows are labelled with practice
    codes and the columns are labelled with dates.

    The `date_count` argument allows restricting to just the N most recent months of
    prescribing data.
    """
    practice_codes, dates = get_practice_codes_and_dates(cursor, date_count)

    values = get_grouped_sum_ndarray(
        cursor,
        row_count=len(practice_codes),
        col_count=len(dates),
        sql=f"""
        SELECT
            practice_id AS row_index,
            date_id AS column_index,
            value
        FROM ({query.to_sql()})
        """,
    )

    return LabelledMatrix(
        values,
        row_labels=practice_codes,
        col_labels=dates,
    )


@functools.cache
def get_practice_codes_and_dates(cursor, date_count):
    """
    Find the N most recent dates for which we have prescribing data and all the practice
    codes which have prescribed during this date range and return them as "index tuples"
    i.e. a tuple where `dates[date_id]` gives you the date with that ID, and similarly
    for practice codes.
    """
    dates = get_dates(cursor, date_count)
    oldest_date = min(d for d in dates if d is not None)
    practice_codes = get_practice_codes(cursor, oldest_date)
    return practice_codes, dates


def get_practice_codes(cursor, oldest_date):
    results = cursor.execute(
        "SELECT id, code FROM practice WHERE latest_prescribing_date >= ?",
        [oldest_date],
    )
    return get_index_tuple(results.fetchall())
