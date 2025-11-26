import contextlib
import pathlib
import sys

import duckdb
from django.conf import settings

from openprescribing.data.utils.duckdb_utils import escape


__all__ = ["get_cursor"]

# Force DuckDB to look for extension modules in the virtualenv rather than the user's
# home directory (!)
DUCKDB_EXTENSION_DIR = f"{sys.prefix}/duckdb"

CREATE_VIEWS_PATH = pathlib.Path(__file__).parent / "create_views.sql"

CONNECTION_MANAGER = None


def get_cursor():
    global CONNECTION_MANAGER
    if CONNECTION_MANAGER is None:
        CONNECTION_MANAGER = ConnectionManager(
            duckdb_file=settings.PRESCRIBING_DATABASE,
            sqlite_file=settings.SQLITE_DATABASE,
            init_sql=CREATE_VIEWS_PATH.read_text(),
        )
    return CONNECTION_MANAGER.get_cursor()


class ConnectionManager:
    def __init__(self, duckdb_file, sqlite_file, init_sql=""):
        self.duckdb_file = duckdb_file
        self.sqlite_file = sqlite_file
        self.init_sql = init_sql
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

        # Run the initialisation SQL to create any views we might need
        self.set_search_path(connection)
        connection.execute(self.init_sql)

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
        # Wrap the cursor in a class that allows it to function as a cache key
        wrapped = CursorCacheKeyWrapper(
            cursor,
            cache_key=(
                # Invalidate the cache if either database file changes
                self.duckdb_last_modified,
                self.sqlite_file.stat().st_mtime,
                # There's a harmless edge case here in that the contents of the SQLite
                # database could change between the time the cursor is created and the
                # time a query is executed. (The same is not true for DuckDB where each
                # database file is immutable.) If this happens then we could end up
                # caching newer data under an old cache key. However subsequent queries
                # will use the newer cache key and so the effect is just a small amount
                # of wasted work in storing a cached value that will never be used. And
                # given how short-lived the cursors are and how infrequently the data
                # changes I expect these to be extremely rare in any case.
            ),
        )
        try:
            yield wrapped
        finally:
            wrapped.close()


class CursorCacheKeyWrapper:
    """
    Our data changes fairly infrequently and many of the queries we run against it are
    quite expensive. This makes it a good candidate for caching. However caching brings
    its own set of problems and so we want a system which:

        (a) is simple to implement;
        (b) doesn't require error-prone invalidation logic.

    By placing the database cursor in a wrapper which is tagged with a cache key (an
    opaque value which changes whenever the contents of the database changes) we can use
    it with Python's standard `functools.lru_cache` decorator:

        @functools.lru_cache
        def function_that_queries_rxdb(cursor, other_arg_1, other_arg_2):
            ...

    This will naturally do the right thing, so long as we ensure that wrapped cursors
    compare equal if and only if their cache keys are equal.
    """

    def __init__(self, cursor, cache_key):
        self.cursor = cursor
        self.cache_key = cache_key

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.cache_key == other.cache_key

    def __hash__(self):
        return hash(self.cache_key)

    def close(self):
        self.cursor.close()
        # We expect the wrapper object to hang around for some time as it's designed to
        # get stored as part of the cache. However we very much don't want the
        # underlying cursor to be stored: we want to discard that as soon as we no
        # longer need it so that it can be garbage collected. So we drop the reference
        # to it immediately after closing.
        self.cursor = None

    def execute(self, *args, **kwargs):
        return self.cursor.execute(*args, **kwargs)

    def sql(self, *args, **kwargs):
        return self.cursor.sql(*args, **kwargs)
