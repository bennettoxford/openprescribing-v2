from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

import openprescribing.data.ingestors.bnf_codes
import openprescribing.data.ingestors.ods
import openprescribing.data.ingestors.prescribing
from openprescribing.data.utils.log_utils import LogHandler


class Command(BaseCommand):
    help = "Run the specified functions to ingest previously fetched data"

    # We can populate this dynamically in future but let's keep it simple for now
    available_ingestors = {
        "bnf_codes": openprescribing.data.ingestors.bnf_codes.ingest,
        "ods": openprescribing.data.ingestors.ods.ingest,
        "prescribing": openprescribing.data.ingestors.prescribing.ingest,
    }

    def add_arguments(self, parser):
        ingestor_choices = ["all", *self.available_ingestors.keys()]
        parser.add_argument(
            "ingestor_names",
            nargs="+",
            choices=ingestor_choices,
            metavar="INGESTOR_NAME",
            help=f"Available options: {', '.join(ingestor_choices)}",
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

    def handle_inner(self, ingestor_names, **options):
        if "all" in ingestor_names:
            ingestor_names = self.available_ingestors.keys()

        log_handler = LogHandler(
            self.stdout.write,
            # Knowing the length of the names upfront allows us to produce more readable
            # logs by justifying them correctly
            max_name_width=max(len(name) for name in ingestor_names),
        )

        for name in ingestor_names:
            ingestor = self.available_ingestors[name]
            with log_handler.capture_logs_as(name):
                ingestor()
