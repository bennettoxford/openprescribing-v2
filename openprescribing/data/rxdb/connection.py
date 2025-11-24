import contextlib
import sys

import duckdb
from django.conf import settings

from openprescribing.data.utils.duckdb_utils import escape


__all__ = ["get_cursor"]

# Force DuckDB to look for extension modules in the virtualenv rather than the user's
# home directory (!)
DUCKDB_EXTENSION_DIR = f"{sys.prefix}/duckdb"

CONNECTION_MANAGER = None


def get_cursor():
    global CONNECTION_MANAGER
    if CONNECTION_MANAGER is None:
        CONNECTION_MANAGER = ConnectionManager(
            duckdb_file=settings.PRESCRIBING_DATABASE,
            sqlite_file=settings.SQLITE_DATABASE,
        )
    return CONNECTION_MANAGER.get_cursor()


class ConnectionManager:
    def __init__(self, duckdb_file, sqlite_file):
        self.duckdb_file = duckdb_file
        self.sqlite_file = sqlite_file
        self.duckdb_last_modified = None
        self.reconnect_if_duckdb_modified()

    def reconnect_if_duckdb_modified(self):
        # Because DuckDB doesn't allow for simultaneously connected writers and readers
        # we can't update database files in-place while the site is running. Instead, we
        # have to treat them as effectively immutable and perform updates by creating a
        # new file alongside the old one and atomically swapping it into place.
        #
        # To detect when this has happened we monitor the modification time of the
        # DuckDB file and, when that changes, we create a new connection pointing to the
        # new file.
        #
        # We don't explicitly close the old connection as it's possbile another thread
        # is still using it at the point we open the new file. We just let it get
        # garbage-collected naturally once all references to it disappear.
        duckdb_last_modified = self.duckdb_file.stat().st_mtime
        if self.duckdb_last_modified == duckdb_last_modified:
            return

        # We make an in-memory connection and then attach our database files into it as
        # read-only
        connection = duckdb.connect(
            config={
                "extension_directory": DUCKDB_EXTENSION_DIR,
            }
        )
        connection.execute(
            f"""
            ATTACH {escape(self.duckdb_file)} AS duckdb_db (TYPE DUCKDB, READ_ONLY);
            ATTACH {escape(self.sqlite_file)} AS sqlite_db (TYPE SQLITE, READ_ONLY);
            """
        )

        # For safety, we disable all the features in DuckDB which allow accessing
        # external data – obviously we have to do this _after_ we've attached our two
        # database files. Given that these are attached read-only there's now no
        # possibility of issuing SQL queries which modify any external state.
        connection.execute("SET enable_external_access = false")

        # Ideally we'd also switch the mode of the in-memory database to read-only
        # using:
        #
        #     SET access_mode = 'READ_ONLY'
        #
        # which would prevent any changes to the in-memory database, but that isn't
        # currently supported. If we wanted to provide an "execute arbitrary SQL"
        # interface (which isn't _totally_ implausible) then we'll need to look at this
        # again. There are possible workarounds if DuckDB hasn't implemented that
        # feature when we get there. See the discussion at:
        # https://github.com/duckdb/duckdb/discussions/19341

        self.duckdb_last_modified = duckdb_last_modified
        self.connection = connection

    @staticmethod
    def set_search_path(cursor):
        # The "search path" is the feature that lets us pretend tables from different
        # databases all live together in one schema. The configuration below says to
        # look up table names in the in-memory database first, then in SQLite and then
        # in the attached DuckDB file.
        cursor.execute("SET search_path = 'memory,sqlite_db,duckdb_db'")

    @contextlib.contextmanager
    def get_cursor(self):
        self.reconnect_if_duckdb_modified()
        cursor = self.connection.cursor()
        # Search path needs to be set per-cursor for some reason; it isn't persistent on
        # the connection.
        self.set_search_path(cursor)
        try:
            yield cursor
        finally:
            cursor.close()
