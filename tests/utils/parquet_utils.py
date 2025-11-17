import pyarrow
import pyarrow.parquet


def parquet_from_dicts(path, list_of_dicts):
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pyarrow.Table.from_pylist(list_of_dicts)
    pyarrow.parquet.write_table(table, path)
