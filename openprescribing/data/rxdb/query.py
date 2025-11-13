import numpy
from scipy.sparse._sparsetools import coo_todense

from openprescribing.data.utils.duckdb_utils import (
    FLOAT_TYPES,
    NUMERIC_TYPES,
    UNSIGNED_INTEGER_TYPES,
)


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


def get_grouped_sum_ndarray(cursor, row_count, col_count, sql, parameters=None):
    """
    Given a SQL query of the form:

        SELECT <row_index>, <column_index>, <numeric_value> ...

    Build a two-dimensional `numpy.ndarray` from the results.

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

    row_type, col_type, value_type = results.types
    assert row_type.id in UNSIGNED_INTEGER_TYPES
    assert col_type.id in UNSIGNED_INTEGER_TYPES
    assert value_type.id in NUMERIC_TYPES
    value_is_float = value_type.id in FLOAT_TYPES

    # Add a filter so that we can guarantee the row and column indexes will be in range
    # (we don't know the actual column names here so we refer to them by position)
    results = results.filter(f"#1 < {row_count} AND #2 < {col_count}")

    # Make a zero-valued accumulator matrix of the right type
    accumulator = numpy.zeros(
        shape=(row_count, col_count),
        dtype=numpy.float64 if value_is_float else numpy.int64,
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
