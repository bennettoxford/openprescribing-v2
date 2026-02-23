# See openprescribing/data/bnf_code_changes/README.txt for context.

import csv

from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Create bnf_code_mapping.csv"

    def handle(self, **kwargs):
        old_to_new = {}

        # By iterating over per-year mappings in reverse order, we can account for
        # presentations changing codes more than once.
        csv_paths = sorted((settings.BNF_CODE_CHANGES_DIR / "raw").glob("*.csv"))
        for path in reversed(csv_paths):
            with path.open() as f:
                for old, new in csv.reader(f):
                    if new in old_to_new:
                        # The new code has been remapped in a future update, so the old
                        # code should map to whatever the new code maps to.
                        old_to_new[old] = old_to_new[new]
                    else:
                        old_to_new[old] = new

        with (settings.BNF_CODE_CHANGES_DIR / "bnf_code_mapping.csv").open("w") as f:
            writer = csv.writer(f)
            writer.writerow(["old_code", "new_code"])
            writer.writerows(sorted(old_to_new.items()))
