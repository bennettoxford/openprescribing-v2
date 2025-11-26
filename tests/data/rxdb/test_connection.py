import functools
import sqlite3

import duckdb

from openprescribing.data.rxdb import connection
from openprescribing.data.utils.filename_utils import get_temp_filename_for


def test_connection_get_cursor(tmp_path, monkeypatch, settings):
    monkeypatch.setattr(connection, "CONNECTION_MANAGER", None)
    monkeypatch.setattr(connection, "CREATE_VIEWS_PATH", tmp_path / "views.sql")
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

    # Create a view that reads from both databases
    connection.CREATE_VIEWS_PATH.write_text(
        """
        CREATE VIEW test_view AS
            SELECT * FROM foo UNION ALL SELECT * FROM bar;
        """
    )

    # Confirm that we can read from it
    with connection.get_cursor() as cursor:
        results = cursor.execute("SELECT * FROM test_view")
        assert results.fetchall() == [(1,), (2,), (3,), (4,), (5,), (6,)]

    # Update the SQLite table and confirm we can read the changes
    sqlite_conn.execute("UPDATE foo SET v = v * 2")
    sqlite_conn.commit()

    with connection.get_cursor() as cursor:
        results = cursor.execute("SELECT * FROM test_view")
        assert results.fetchall() == [(2,), (4,), (6,), (4,), (5,), (6,)]

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

    with connection.get_cursor() as cursor:
        results = cursor.execute("SELECT * FROM test_view")
        assert results.fetchall() == [(2,), (4,), (6,), (10,), (11,), (12,)]


def test_get_cursor_cache_key_wrapper(tmp_path):
    duckdb_file = tmp_path / "data.duckdb"
    sqlite_file = tmp_path / "data.sqlite"

    # Write some values into the SQLite database
    sqlite_conn = sqlite3.connect(sqlite_file)
    sqlite_conn.executescript(
        """
        PRAGMA journal_mode = WAL;
        CREATE TABLE foo (v INT);
        INSERT INTO foo VALUES (1), (2), (3);
        """
    )

    # Write some values into the DuckDB database
    duckdb_conn = duckdb.connect(duckdb_file)
    duckdb_conn.sql(
        """
        CREATE TABLE bar (v INT);
        INSERT INTO bar VALUES (4), (5), (6);
        """
    )
    duckdb_conn.close()

    manager = connection.ConnectionManager(
        duckdb_file=duckdb_file,
        sqlite_file=sqlite_file,
    )

    # Confirm that query results are cached as expected

    @functools.cache
    def cached_query(cursor, query):
        return cursor.execute(query).fetchall()

    with manager.get_cursor() as cursor:
        results = cached_query(cursor, "SELECT * FROM foo UNION ALL SELECT * FROM bar")
        assert results == [(1,), (2,), (3,), (4,), (5,), (6,)]

    assert cached_query.cache_info().hits == 0
    assert cached_query.cache_info().misses == 1

    # Confirm that an identical query hits the cache rather than the database
    with manager.get_cursor() as cursor:
        results = cached_query(cursor, "SELECT * FROM foo UNION ALL SELECT * FROM bar")
        assert results == [(1,), (2,), (3,), (4,), (5,), (6,)]

    assert cached_query.cache_info().hits == 1
    assert cached_query.cache_info().misses == 1

    # Replace the DuckDB file with a new one
    tmp_file = get_temp_filename_for(duckdb_file)
    duckdb_conn = duckdb.connect(tmp_file)
    duckdb_conn.sql(
        """
        CREATE TABLE bar (v INT);
        INSERT INTO bar VALUES (10), (11), (12);
        """
    )
    duckdb_conn.close()
    tmp_file.replace(duckdb_file)

    # Confirm this results in a cache miss and gives fresh results
    with manager.get_cursor() as cursor:
        results = cached_query(cursor, "SELECT * FROM foo UNION ALL SELECT * FROM bar")
        assert results == [(1,), (2,), (3,), (10,), (11,), (12,)]

    assert cached_query.cache_info().hits == 1
    assert cached_query.cache_info().misses == 2

    # Update the SQLite file and commit but don't force a WAL checkpoint
    sqlite_conn.execute("UPDATE foo SET v = v * 2")
    sqlite_conn.commit()

    # Confirm that this still gives the previous cached result
    with manager.get_cursor() as cursor:
        results = cached_query(cursor, "SELECT * FROM foo UNION ALL SELECT * FROM bar")
        assert results == [(1,), (2,), (3,), (10,), (11,), (12,)]

    assert cached_query.cache_info().hits == 2
    assert cached_query.cache_info().misses == 2

    # Force a WAL checkpoint which will update the main database file
    sqlite_conn.execute("PRAGMA wal_checkpoint(FULL)")

    # Confirm this results in a cache miss and gives fresh results
    with manager.get_cursor() as cursor:
        results = cached_query(cursor, "SELECT * FROM foo UNION ALL SELECT * FROM bar")
        assert results == [(2,), (4,), (6,), (10,), (11,), (12,)]

    assert cached_query.cache_info().hits == 2
    assert cached_query.cache_info().misses == 3
