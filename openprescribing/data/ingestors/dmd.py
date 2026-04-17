import logging

import duckdb
from django.conf import settings
from django.db import models, transaction

from openprescribing.data.models import IngestedFile
from openprescribing.data.models import dmd as dmd_models_module
from openprescribing.data.utils.duckdb_utils import escape


log = logging.getLogger(__name__)


def ingest(force=False):
    latest_dir = max(settings.DOWNLOAD_DIR.glob("dmd/*"))

    if not force and (
        not latest_dir or latest_dir.name <= IngestedFile.get_by_name("dmd")
    ):
        log.debug("Found no new data to ingest")
        return

    log.info(f"Preparing to ingest files: {latest_dir.name}")

    conn = duckdb.connect()

    with transaction.atomic(using="data"):
        for model in get_dmd_models():
            # For each model, we delete all existing instances, and (re)create new ones
            # from the data in the parquet files.
            log.info(f"Ingesting {model.__name__}")
            model.objects.all().delete()
            table_name = model._meta.db_table
            latest_file = latest_dir / f"{table_name}.parquet"
            if not latest_file.exists():
                # The test data does not contain data for every single dm+d data type.
                continue
            records = (
                conn.sql(f"SELECT * FROM read_parquet({escape(latest_file)})")
                .to_arrow_table()
                .to_pylist()
            )
            instances = [build_instance(model, record) for record in records]
            model.objects.bulk_create(instances)

        IngestedFile.set_by_name("dmd", latest_dir.name)

    conn.close()


def get_dmd_models():
    """Return list of all models defined in openprescribing.data.models.dmd."""

    return [
        model
        for model in vars(dmd_models_module).values()
        if isinstance(model, type)
        and issubclass(model, models.Model)
        and not model._meta.abstract
    ]


def build_instance(model, record):
    """Given a model class and a dictionary of keys/values, create an instance of the class.

    Some munging of the dictionary may be necessary to match the fields that Django expects.
    """

    if model == dmd_models_module.ReimbInfo:
        # The ReimbInfo.ltd_stab field is present in the data but is always NULL.  It is
        # not clear what type it should have so we've not included it in the model
        # definition, and so we shouldn't try to ingest it.
        assert record["ltd_stab"] is None
        del record["ltd_stab"]

    for f in model._meta.fields:
        if isinstance(f, models.BooleanField):
            # Boolean fields are sometimes NULL in the data.  We convert these to False
            # for consistency.
            record[f.attname] = bool(record[f.attname])
        if isinstance(f, models.ForeignKey):
            # ForeignKey attribute names don't match the column names from the parquet
            # data that we are ingesting.
            #
            # For instance, the table in vmp.parquet has a column called "vtmid", while
            # the VMP class has a ForeignKey field called "vtm".  Django insists on
            # naming the corresponding attribute "vtm_id", so in order to create a VMP
            # object from the data in the table in vmp.parquet, we have to rename the
            # record key from "vtmid" to "vtm_id".

            if model == dmd_models_module.ReimbInfo and f.attname == "dnd_id":
                # For almost all ForeignKey columns, the column name in the raw data
                # ends "id" or "cd" (eg "vtmid" or "basiscd").  The exception is the dnd
                # column in reimb_info.parquet.  To minimise surprise, we have changed
                # the database column to be called "dndcd", and so we need to account
                # for that here.
                key = "dnd"
            else:
                key = f.db_column
            record[f.attname] = record[key]
            del record[key]

    if "desc" in record:
        # "desc" is a SQL keyword, so renaming it to "descr" (for "description") will
        # make working with the data via SQL easier.
        record["descr"] = record["desc"]
        del record["desc"]

    return model(**record)
