import datetime
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

import openprescribing.data.fetchers.prescribing


class Command(BaseCommand):
    help = "Run the specified fetcher functions to fetch external data"

    # We can populate this dynamically in future but let's keep it simple for now
    available_fetchers = {
        "prescribing": openprescribing.data.fetchers.prescribing.fetch,
    }

    def add_arguments(self, parser):
        fetcher_choices = ["all", *self.available_fetchers.keys()]
        parser.add_argument(
            "fetcher_names",
            nargs="+",
            choices=fetcher_choices,
            metavar="FETCHER_NAME",
            help=f"Available options: {', '.join(fetcher_choices)}",
        )

    def handle(self, fetcher_names, **options):
        if "all" in fetcher_names:
            fetcher_names = self.available_fetchers.keys()

        log_handler = LogHandler(
            self.stdout.write,
            # Knowing the length of the names upfront allows us to produce more readable
            # logs by justifying them correctly
            max_name_width=max(len(name) for name in fetcher_names),
        )

        for name in fetcher_names:
            fetcher = self.available_fetchers[name]
            with log_handler.capture_logs_as(name):
                fetcher(settings.DOWNLOAD_DIR)


class LogHandler:
    def __init__(self, writer, max_name_width=0):
        self.writer = writer
        self.max_name_width = max_name_width

        root_module = __name__.partition(".")[0]
        self.logger = logging.getLogger(root_module)
        self.log_handler = logging.Handler()
        self.log_handler.emit = self.emit
        self.current_name = None

    def emit(self, record):
        self.write(self.log_handler.format(record))

    def write(self, line):
        self.writer(
            f"{datetime.datetime.now(datetime.UTC):%Y-%m-%dT%H:%M:%S} "
            f"[{self.current_name.rjust(self.max_name_width)}] "
            f"{line}"
        )

    def capture_logs_as(self, name):
        self.current_name = name
        return self

    def __enter__(self):
        self.logger.setLevel("DEBUG")
        self.logger.addHandler(self.log_handler)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.logger.removeHandler(self.log_handler)
