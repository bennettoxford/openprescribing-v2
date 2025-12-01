import os

from django.conf import settings
from django.core.management.base import BaseCommand

from openprescribing.data.rxdb.connection import CREATE_VIEWS_PATH, DUCKDB_EXTENSION_DIR
from openprescribing.data.utils.duckdb_utils import escape


class Command(BaseCommand):
    help = "Open a DuckDB shell configured in the same way as an RXDB connection"

    def add_arguments(self, parser):
        parser.add_argument(
            "--writable",
            action="store_true",
            help="Open database files in writable mode",
        )

    def handle(self, writable=False, **options):
        self.stderr.write(f"Attaching DuckDB file at: {settings.PRESCRIBING_DATABASE}")
        self.stderr.write(f"Attaching SQLite file at: {settings.SQLITE_DATABASE}")
        self.stderr.write(f"Executing SQL from: {CREATE_VIEWS_PATH}")

        read_write_config = ", READ_ONLY" if not writable else ""
        create_views_sql = CREATE_VIEWS_PATH.read_text()

        setup_sql = f"""\
        SET extension_directory = {escape(DUCKDB_EXTENSION_DIR)};

        ATTACH {escape(settings.PRESCRIBING_DATABASE)} AS duckdb_db
            (TYPE DUCKDB {read_write_config});

        ATTACH {escape(settings.SQLITE_DATABASE)} AS sqlite_db
            (TYPE SQLITE {read_write_config});

        SET search_path = 'memory,sqlite_db,duckdb_db';

        {create_views_sql}
        """

        try:
            # Replace the current process with the DuckDB CLI
            os.execvp("duckdb", ["duckdb", "--cmd", setup_sql])
        except FileNotFoundError as e:  # pragma: no cover
            e.add_note(
                "\nDuckDB CLI tool not found. Have you set up the develepment "
                "environment?\n\n    just devenv\n"
            )
            raise
