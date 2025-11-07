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
        for name in fetcher_names:
            fetcher = self.available_fetchers[name]
            fetcher(settings.DOWNLOAD_DIR)
