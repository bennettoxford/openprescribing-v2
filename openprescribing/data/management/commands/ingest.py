import django.db
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

import openprescribing.data.ingestors
from openprescribing.data.utils.log_utils import LogHandler


class Command(BaseCommand):
    help = "Run the specified functions to ingest previously fetched data"

    # keep a reference so that we can easily monkeypatch
    available_ingestors = openprescribing.data.ingestors.available_ingestors

    def add_arguments(self, parser):
        ingestor_choices = ["all", *self.available_ingestors.keys()]
        parser.add_argument(
            "ingestor_names",
            nargs="+",
            choices=ingestor_choices,
            metavar="INGESTOR_NAME",
            help=f"Available options: {', '.join(ingestor_choices)}",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-ingesting existing data",
        )
        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            help="Don't produce output if there is nothing new to ingest",
        )

    def handle(self, *args, **options):
        try:
            return self.handle_inner(*args, **options)
        except OperationalError as e:  # pragma: no cover
            if str(e).startswith("no such table:"):
                e.add_note(
                    "\nYou may have unapplied migrations, which you can fix by "
                    "running:\n\n"
                    "    just manage migrate --database data\n"
                )
            raise

    def handle_inner(self, ingestor_names, force=False, quiet=False, **options):
        if "all" in ingestor_names:
            ingestor_names = self.available_ingestors.keys()

        log_handler = LogHandler(
            self.stdout.write,
            log_level="INFO" if quiet else "DEBUG",
            # Knowing the length of the names upfront allows us to produce more readable
            # logs by justifying them correctly
            max_name_width=max(len(name) for name in ingestor_names),
        )

        for name in ingestor_names:
            ingestor = self.available_ingestors[name]
            with log_handler.capture_logs_as(name):
                ingestor(force=force)
                ensure_main_database_file_is_updated()


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
