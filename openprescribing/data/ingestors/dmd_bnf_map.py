import logging

import duckdb
from django.conf import settings
from django.db import transaction

from openprescribing.data.models import DmdBnfMap, IngestedFile
from openprescribing.data.utils.duckdb_utils import escape


log = logging.getLogger(__name__)


def ingest(force=False):
    latest_file = max(settings.DOWNLOAD_DIR.glob("dmd_bnf_map/*"))

    if not force and (
        not latest_file or latest_file.name <= IngestedFile.get_by_name("dmd_bnf_map")
    ):
        log.debug("Found no new data to ingest")
        return

    log.info(f"Preparing to ingest files: {latest_file.name}")

    conn = duckdb.connect()
    sql = f"""
    SELECT "SNOMED Code" AS dmd_id, "BNF Code" AS bnf_code
    FROM read_parquet({escape(latest_file)})
    """
    records = conn.sql(sql).to_arrow_table().to_pylist()
    instances = [
        DmdBnfMap(**record)
        for record in records
        # The raw data can contain partially blank rows, which we ignore.
        if record["dmd_id"] and record["bnf_code"]
    ]

    with transaction.atomic(using="data"):
        DmdBnfMap.objects.all().delete()
        DmdBnfMap.objects.bulk_create(instances)
        IngestedFile.set_by_name("dmd_bnf_map", latest_file.name)

    conn.close()
