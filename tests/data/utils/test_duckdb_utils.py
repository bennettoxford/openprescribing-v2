import json

import duckdb

from openprescribing.data.utils.duckdb_utils import ProfilingConnection


def test_profiling_connection(tmp_path):
    conn = ProfilingConnection(duckdb.connect(), tmp_path)
    conn.sql("SELECT 1")
    conn.sql("SELECT 2")
    conn.close()
    q1, q2 = [json.loads(q.read_text()) for q in sorted(tmp_path.iterdir())]
    assert q1["query_name"] == "SELECT 1"
    assert q2["query_name"] == "SELECT 2"
