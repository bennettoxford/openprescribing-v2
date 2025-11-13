import sqlite3

import duckdb

from openprescribing.data import rxdb
from openprescribing.data.rxdb import connection
from openprescribing.data.utils.filename_utils import get_temp_filename_for


def test_connection_get_cursor(tmp_path, monkeypatch, settings):
    monkeypatch.setattr(connection, "CONNECTION_MANAGER", None)
    settings.PRESCRIBING_DATABASE = tmp_path / "prescribing.duckdb"
    settings.SQLITE_DATABASE = tmp_path / "data.sqlite"

    # Write some values into the SQLite database
    sqlite_conn = sqlite3.connect(settings.SQLITE_DATABASE)
    sqlite_conn.executescript(
        """
        CREATE TABLE foo (v INT);
        INSERT INTO foo VALUES (1), (2), (3);
        """
    )

    # Write some values into the DuckDB database
    duckdb_conn = duckdb.connect(settings.PRESCRIBING_DATABASE)
    duckdb_conn.sql(
        """
        CREATE TABLE bar (v INT);
        INSERT INTO bar VALUES (4), (5), (6);
        """
    )
    duckdb_conn.close()

    # Confirm that we can read from both
    with rxdb.get_cursor() as cursor:
        results = cursor.execute("SELECT * FROM foo UNION ALL SELECT * FROM bar")
        results.fetchall() == [(1,), (2,), (3,), (4,), (5,), (6,)]

    # Update the SQLite table and confirm we can read the changes
    sqlite_conn.execute("UPDATE foo SET v = v * 2")

    with rxdb.get_cursor() as cursor:
        results = cursor.execute("SELECT * FROM foo UNION ALL SELECT * FROM bar")
        results.fetchall() == [(2,), (4,), (6,), (4,), (5,), (6,)]

    # Replace the DuckDB file and confirm that we pick up the new file and can read the
    # changes
    tmp_file = get_temp_filename_for(settings.PRESCRIBING_DATABASE)
    duckdb_conn = duckdb.connect(tmp_file)
    duckdb_conn.sql(
        """
        CREATE TABLE bar (v INT);
        INSERT INTO bar VALUES (10), (11), (12);
        """
    )
    duckdb_conn.close()
    tmp_file.replace(settings.PRESCRIBING_DATABASE)

    with rxdb.get_cursor() as cursor:
        results = cursor.execute("SELECT * FROM foo UNION ALL SELECT * FROM bar")
        results.fetchall() == [(2,), (4,), (6,), (10,), (11,), (12,)]
