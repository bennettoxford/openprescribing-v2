import functools

import numpy as np
from scipy.sparse._sparsetools import coo_todense

from openprescribing.data.rxdb.labelled_matrix import LabelledMatrix
from openprescribing.data.utils.duckdb_utils import (
    FLOAT_TYPES,
    NUMERIC_TYPES,
    UNSIGNED_INTEGER_TYPES,
)


__all__ = ["get_practice_date_matrix"]


# Sets the number of rows we fetch in each batch from DuckDB. There's no perfect answer
# to what size these batches should be, but here are some considerations:
#
#  * They should probably be a multiple of 2048 as that's the natural DuckDB "data
#    chunk" size (see https://duckdb.org/docs/stable/clients/c/data_chunk).
#
#  * If they are too small then we will spend too much time hopping back and forth
#    between fast native code and Python and that will slow things down.
#
#  * If they are too large then we force DuckDB to consume lots of memory while building
#    the batch and, observationally, this seems to be slower (maybe while we're
#    processing each batch DuckDB is preparing the next one in parallel?).
#
# The current value was determined by some crude profiling and a simple binary search to
# land on what looked like the optimal value. It may well be possible to improve it.
RECORD_BATCH_SIZE = 2048 * 64

# The largest of these matrices are about 16MB in size (140 dates x 15,000 practices x 8
# bytes per value). Caching the most recently used 128 only takes 2GB of RAM and should
# mean we can serve common queries from the cache.
PRACTICE_DATE_MATRIX_CACHE_SIZE = 128


@functools.lru_cache(maxsize=PRACTICE_DATE_MATRIX_CACHE_SIZE)
def get_practice_date_matrix(cursor, sql, parameters=None, date_count=None):
    """
    Given a SQL query of the form:

        SELECT practice_id, date_id, value FROM ...

    Sum all the values for each practice and date and return a `LabelledMatrix` of these
    values, where the rows are labelled with practice codes and the columns are labelled
    with dates.

    The `date_count` argument allows restricting to just the N most recent months of
    prescribing data.

    Note that the exact form of the SQL doesn't matter so long as it selects at least
    three columns with those names.
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
        FROM ({sql})
        """,
        parameters=parameters,
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


def get_dates(cursor, date_count):
    results = cursor.execute(
        "SELECT id, date FROM date ORDER BY date DESC LIMIT ?",
        [date_count if date_count is not None else 9999999],
    )
    return get_index_tuple(results.fetchall())


def get_practice_codes(cursor, oldest_date):
    results = cursor.execute(
        "SELECT id, code FROM practice WHERE latest_prescribing_date >= ?",
        [oldest_date],
    )
    return get_index_tuple(results.fetchall())


def get_index_tuple(index_value_pairs):
    """
    Given a list of (<index>, <value>) pairs return a tuple:

        (<value_0>, <value_1>, <value_2> ...)

    Place each value at its specified index. Where there is no value for a given index
    use `None`.
    """
    index_to_value = {index: value for index, value in index_value_pairs}
    assert index_to_value, "No prescribing data in database"
    all_indexes = range(0, max(index_to_value.keys()) + 1)
    return tuple(index_to_value.get(index) for index in all_indexes)


def get_grouped_sum_ndarray(cursor, row_count, col_count, sql, parameters=None):
    """
    Given a SQL query of the form:

        SELECT row_index, column_index, value FROM ...

    Build a two-dimensional `np.ndarray` from the results.

    It's expected that we'll see multiple values for the same coordinate in the array
    and these values will be summed together. The effect is thus the same as doing:

        SELECT row_index, column_index, SUM(value)
        FROM ...
        GROUP BY row_index, column_index

    This is the key data-heavy operation which OpenPrescribing needs to perform and so
    it's worth a bit of complexity here to make this fast.
    """
    # The `sql` method is lazy so it parses the query and determines the column types
    # but doesn't yet execute it
    results = cursor.sql(sql, params=parameters)

    assert results.columns == ["row_index", "column_index", "value"]
    row_type, col_type, value_type = results.types
    assert row_type.id in UNSIGNED_INTEGER_TYPES
    assert col_type.id in UNSIGNED_INTEGER_TYPES
    assert value_type.id in NUMERIC_TYPES
    value_is_float = value_type.id in FLOAT_TYPES

    # Add a filter so that we can guarantee the row and column indexes will be in range
    results = results.filter(f"row_index < {row_count} AND column_index < {col_count}")

    # Make a zero-valued accumulator matrix of the right type
    accumulator = np.zeros(
        shape=(row_count, col_count),
        dtype=np.float64 if value_is_float else np.int64,
    )

    # Prepare some values that `coo_todense` needs (based on reading the SciPy source)
    accumulator_ravel = accumulator.ravel("A")
    is_fortran_order = int(accumulator.flags.f_contiguous)

    for batch in results.fetch_record_batch(rows_per_batch=RECORD_BATCH_SIZE):
        row_indexes = batch.column(0).to_numpy()
        col_indexes = batch.column(1).to_numpy()
        values = batch.column(2).to_numpy()

        # Add each batch of results into our accumulator matrix using a fast routine
        # borrowed from `scipy.sparse`
        coo_todense(
            row_count,
            col_count,
            len(values),
            row_indexes,
            col_indexes,
            values,
            accumulator_ravel,
            is_fortran_order,
        )

    return accumulator
