import itertools
from pathlib import Path


# Types taken from:
# https://duckdb.org/docs/stable/sql/data_types/numeric
UNSIGNED_INTEGER_TYPES = {"utinyint", "usmallint", "uinteger", "ubigint", "uhugeint"}
SIGNED_INTEGER_TYPES = {"tinyint", "smallint", "integer", "bigint", "hugeint"}
INTEGER_TYPES = UNSIGNED_INTEGER_TYPES | SIGNED_INTEGER_TYPES
FLOAT_TYPES = {"float", "double"}
NUMERIC_TYPES = FLOAT_TYPES | INTEGER_TYPES


def escape(s):
    # DuckDB doesn't accept parameter placeholders for filenames in queries so we have
    # to escape them manually
    return "'" + str(s).replace("'", "''") + "'"


class ProfilingConnection:
    """
    This class wraps an instance of `DuckDBPyConnection` and writes profiling
    information to a JSON file each time the `.sql` method is called.

    For example:

    ```python
    conn = ProfilingConnection(duckdb.connect(), "queries")
    conn.sql("SELECT ...")  # writes queries/query_001.json
    conn.sql("SELECT ...")  # writes queries/query_002.json

    This class is intended for experimental use; either locally or in a production-like
    environment, wrap the connection, run the code, and investigate the profiling
    information. This class is not intended for production use.
    """

    def __init__(self, conn, profile_dir):
        self._conn = conn
        self._profile_dir = Path(profile_dir).resolve()
        self._counter = itertools.count(1)

        self._conn.enable_profiling()

    def sql(self, *args, **kwargs):
        # Instances of DuckDBPyRelation, which are returned by DuckDBPyConnection.sql,
        # are lazy. We have to execute them here to get the profiling information now.
        rel = self._conn.sql(*args, **kwargs).execute()
        info = self._conn.get_profiling_information()
        f_out = self._profile_dir / f"query_{next(self._counter):03d}.json"
        f_out.write_text(info)
        return rel

    def __getattr__(self, name):
        return getattr(self._conn, name)
