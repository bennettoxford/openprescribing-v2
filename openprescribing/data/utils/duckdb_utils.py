def escape(s):
    # DuckDB doesn't accept parameter placeholders for filenames in queries so we have
    # to escape them manually
    return "'" + str(s).replace("'", "''") + "'"
