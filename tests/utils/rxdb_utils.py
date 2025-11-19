import datetime
import textwrap

import duckdb
import pyarrow

from openprescribing.data.ingestors.prescribing import ingest_sources


PRESCRIBING_SOURCE_SCHEMA = pyarrow.schema(
    [
        ("bnf_code", pyarrow.string()),
        ("snomed_code", pyarrow.int64()),
        ("date", pyarrow.date32()),
        ("practice_code", pyarrow.string()),
        ("quantity_value", pyarrow.float32()),
        ("items", pyarrow.uint16()),
        ("quantity", pyarrow.float32()),
        ("net_cost", pyarrow.uint32()),
        ("actual_cost", pyarrow.uint32()),
    ]
)

PRESCRIBING_SOURCE_DEFAULTS = {
    "bnf_code": "",
    "snomed_code": 0,
    "date": datetime.date(2000, 1, 1),
    "practice_code": "",
    "quantity_value": 0.0,
    "items": 0,
    "quantity": 0.0,
    "net_cost": 0,
    "actual_cost": 0,
}

LIST_SIZE_SOURCE_SCHEMA = pyarrow.schema(
    [
        ("date", pyarrow.date32()),
        ("practice_code", pyarrow.string()),
        ("total", pyarrow.uint32()),
    ]
)

LIST_SIZE_SOURCE_DEFAULTS = {
    "date": datetime.date(2000, 1, 1),
    "practice_code": "",
    "total": 0,
}


class RXDBFixture:
    """
    Provides a test fixture which can used in place of the default `rxdb` instance

    Note that unlike the real thing this doesn't currently have the SQLite database
    attached. It is possible to get this working, but it requires a couple of changes:

     * The test SQLite database needs to be on disk, not in memory, as DuckDB can't
       currently attach to in-memory databases. (I think this might be an easy fix, but
       I don't know how long it will take to get the patch landed in DuckDB.)

     * Tests need to run in "transaction mode" using:
       @pytest.mark.django_db(databases=["data"], transaction=True)
       This is because in order for DuckDB to see changes in the SQLite database they
       need to be commited, rather than held in temporary transactions.

    Given that we don't currently need this feature I'm holding off supporting it.
    """

    def __init__(self):
        self.conn = duckdb.connect()
        self.has_data = False

    def get_cursor(self):
        if not self.has_data:  # pragma: no cover
            msg = """\
            No prescribing data loaded into `rxdb` fixture, use:

                rxdb.ingest(
                    [
                        {...},
                        ...
                    ]
                )

            Missing keys take default values so at a minimum you can load a single row
            of default data with:

                rxdb.ingest([{}])

            """
            raise RuntimeError(textwrap.dedent(msg))
        return self.conn.cursor()

    def ingest(self, prescribing_data, list_size_data=()):
        rxdb_ingest(
            self.conn,
            prescribing_data=prescribing_data,
            list_size_data=list_size_data,
        )
        self.has_data = True


def rxdb_ingest(conn, prescribing_data=(), list_size_data=()):
    """
    Given a DuckDB connection and some prescribing and list size data as lists of
    dictionaries, ingest that data into the database using the same function used in
    production.
    """
    prescribing_data = prepare_data(prescribing_data, PRESCRIBING_SOURCE_DEFAULTS)
    list_size_data = prepare_data(list_size_data, LIST_SIZE_SOURCE_DEFAULTS)
    prescribing_source = pyarrow.Table.from_pylist(
        prescribing_data, schema=PRESCRIBING_SOURCE_SCHEMA
    )
    list_size_source = pyarrow.Table.from_pylist(
        list_size_data, schema=LIST_SIZE_SOURCE_SCHEMA
    )
    # Register the PyArrow Tables so they can be queried like any other table in DuckDB
    conn.register("prescribing_source", prescribing_source)
    conn.register("list_size_source", list_size_source)
    ingest_sources(conn)
    conn.unregister("prescribing_source")
    conn.unregister("list_size_source")


def prepare_data(data, defaults):
    prepared = []
    for input_row in data:
        row = defaults | input_row
        if isinstance(row["date"], str):
            row["date"] = datetime.date.fromisoformat(row["date"])
        prepared.append(row)
    return prepared
