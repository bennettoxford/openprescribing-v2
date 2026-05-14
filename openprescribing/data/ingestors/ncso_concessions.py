import json
import logging
import re

from django.conf import settings
from django.db import transaction

from openprescribing.data.models.core import IngestedFile
from openprescribing.data.models.ncso_concessions import NCSOConcessions


log = logging.getLogger(__name__)


def ingest(force=False):
    ncso_concessions_file = sorted(settings.DOWNLOAD_DIR.glob("ncso_concessions/*"))[-1]
    date = file_date(ncso_concessions_file)

    if not force and (not date or date <= IngestedFile.get_by_name("ncso_concessions")):
        log.debug("No new NCSO Concessions data found to ingest")
        return

    with open(ncso_concessions_file) as f:
        ncso_concessions_raw = json.load(f)

        ncso_concessions = [
            NCSOConcessions(
                date=c["fields"]["date"],
                vmpp=c["fields"]["vmpp"],
                price_pence=c["fields"]["price_pence"],
            )
            for c in ncso_concessions_raw
        ]

    with transaction.atomic(using="data"):
        NCSOConcessions.objects.all().delete()
        NCSOConcessions.objects.bulk_create(ncso_concessions)
        IngestedFile.set_by_name("ncso_concessions", date)

    log.info(
        f"Imported {len(NCSOConcessions.objects.all())} NCSO Concessions from {date}"
    )


def file_date(filename):
    match = re.match(r".*ncso_concessions_(\d{4}-\d{2}-\d{2})\.json", str(filename))
    assert match, f"Expecting a filename containing an ISO date: {filename}"
    return match.group(1)
