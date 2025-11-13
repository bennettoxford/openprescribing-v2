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
