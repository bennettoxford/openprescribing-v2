import datetime

import pyarrow

from openprescribing.data.ingestors.prescribing import ingest_prescribing_source


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


def rxdb_ingest(conn, prescribing_data=()):
    """
    Given a DuckDB connection and some prescribing data as a list of dictionaries ingest
    that data into the database using the same function used in production.
    """
    prescribing_data = prepare_prescribing_data(prescribing_data)
    prescribing_source = pyarrow.Table.from_pylist(
        prescribing_data, schema=PRESCRIBING_SOURCE_SCHEMA
    )
    # Register the PyArrow Table so it can be queried like any other table in DuckDB
    conn.register("prescribing_source", prescribing_source)
    ingest_prescribing_source(conn)
    conn.unregister("prescribing_source")


def prepare_prescribing_data(data):
    prepared = []
    for input_row in data:
        row = PRESCRIBING_SOURCE_DEFAULTS | input_row
        if isinstance(row["date"], str):
            row["date"] = datetime.date.fromisoformat(row["date"])
        prepared.append(row)
    return prepared
