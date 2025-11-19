from django.conf import settings
from django.core.management.base import BaseCommand

import openprescribing.data.fetchers.bnf_codes
import openprescribing.data.fetchers.list_size
import openprescribing.data.fetchers.ods
import openprescribing.data.fetchers.prescribing
from openprescribing.data.utils.log_utils import LogHandler


class Command(BaseCommand):
    help = "Run the specified fetcher functions to fetch external data"

    # We can populate this dynamically in future but let's keep it simple for now
    available_fetchers = {
        "bnf_codes": openprescribing.data.fetchers.bnf_codes.fetch,
        "list_size": openprescribing.data.fetchers.list_size.fetch,
        "ods": openprescribing.data.fetchers.ods.fetch,
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
