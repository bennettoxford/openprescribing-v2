import logging

import duckdb
from django.conf import settings
from django.db import transaction

from openprescribing.data.models import BNFCode, IngestedFile
from openprescribing.data.utils.duckdb_utils import escape


log = logging.getLogger(__name__)


def ingest(force=False):
    bnf_codes_files = settings.DOWNLOAD_DIR.glob("bnf_codes/*.parquet")
    latest_file = max(bnf_codes_files, default=None)

    if not force and (
        not latest_file or latest_file.name <= IngestedFile.get_by_name("bnf_codes")
    ):
        log.debug("Found no new data to ingest")
        return

    log.info(f"Preparing to ingest file: {latest_file.name}")

    conn = duckdb.connect()
    conn.sql(
        f"CREATE VIEW bnf_codes AS SELECT * FROM read_parquet({escape(latest_file)})"
    )

    with transaction.atomic(using="data"):
        BNFCode.objects.all().delete()
        ingest_bnf_codes(conn)
        IngestedFile.set_by_name("bnf_codes", latest_file.name)

    conn.close()

    count = BNFCode.objects.count()
    log.info(f"Ingested {count:,} BNF codes")


def ingest_bnf_codes(conn):
    # CHAPTER, SECTION, PARAGRAPH etc.
    for level in BNFCode.Level:
        name_column = f"BNF_{level.name}"
        code_column = f"BNF_{level.name}_CODE"
        results = conn.sql(
            f"SELECT DISTINCT {code_column}, {name_column} FROM bnf_codes"
        )
        for code, name in results.fetchall():
            BNFCode(code=code, name=name, level=level).save()
