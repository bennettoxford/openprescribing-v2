from django.conf import settings
from django.core.management.base import BaseCommand

import openprescribing.data.fetchers
from openprescribing.data.utils.log_utils import LogHandler


class Command(BaseCommand):
    help = "Run the specified fetcher functions to fetch external data"

    # keep a reference here so that we can easily monkeypatch in tests
    available_fetchers = openprescribing.data.fetchers.available_fetchers

    def add_arguments(self, parser):
        fetcher_choices = ["all", *self.available_fetchers.keys()]
        parser.add_argument(
            "fetcher_names",
            nargs="+",
            choices=fetcher_choices,
            metavar="FETCHER_NAME",
            help=f"Available options: {', '.join(fetcher_choices)}",
        )
        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            help="Don't produce output if there is nothing new to fetch",
        )

    def handle(self, fetcher_names, quiet=False, **options):
        if "all" in fetcher_names:
            fetcher_names = self.available_fetchers.keys()

        log_handler = LogHandler(
            self.stdout.write,
            log_level="INFO" if quiet else "DEBUG",
            # Knowing the length of the names upfront allows us to produce more readable
            # logs by justifying them correctly
            max_name_width=max(len(name) for name in fetcher_names),
        )

        for name in fetcher_names:
            fetcher = self.available_fetchers[name]
            with log_handler.capture_logs_as(name):
                fetcher(settings.DOWNLOAD_DIR)
