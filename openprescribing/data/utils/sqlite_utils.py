import django.db


def ensure_main_database_file_is_updated():
    # Not every write to a SQLite database automatically causes the `.sqlite` file to be
    # updated. When running in WAL mode, writes go to the `.wal` file in the first
    # instance and only when this gets to a certain size do they get persisted in the
    # main `.sqlite` file. This helps SQLite support large numbers of writes from
    # multiple writers. However, we have only a single, infrequent writer and there are
    # benefits to ensuring that all writes get immediately persisted in the `.sqlite`
    # file:
    #
    #  1. The last-modified timestamp on the database file becomes an accurate
    #     indication of when any data last changed, which is useful for caching
    #     purposes.
    #
    #  2. Copying the single SQLite file always results in a full up-to-date copy of the
    #     current production data.
    #
    # If there are no new commits in the WAL then this is a no-op and the last-modified
    # timestamp remains unchanged.
    conn = django.db.connections["data"]
    with conn.cursor() as cursor:
        # We use FULL (which ensures that the process completes) rather than default
        # PASSIVE (which is best effort only). This blocks other writers but not other
        # readers, which is fine for our purposes as `ingest` is the only writer.
        # https://sqlite.org/pragma.html#pragma_wal_checkpoint
        cursor.execute("PRAGMA wal_checkpoint(FULL)")
