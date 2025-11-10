import duckdb

from openprescribing.data.utils.duckdb_utils import escape


def csv_to_parquet(
    csv_filename,
    parquet_filename,
    encoding="utf-8",
    parquet_version=2,
    compression="zstd",
    compression_level=10,
):
    """
    Reads a CSV file and writes it out as a Parquet file

    Deliberately disables any form of type-guessing and leaves all column types as
    strings so that the resulting Parquet file is as close as possible to a faithful
    archive copy of the original CSV while being much smaller and faster to query.

    Uses sensible default values configuration values for the Parquet file.
    """
    assert isinstance(parquet_version, int)
    assert isinstance(compression_level, int)
    duckdb.sql(
        f"""
        COPY (
            SELECT * FROM
            read_csv(
              {escape(csv_filename)},
              header=true,
              encoding={escape(encoding)},
               /* disable type guessing and leave columns as strings */
              all_varchar=true
            )
        )
        TO {escape(parquet_filename)} (
            FORMAT 'PARQUET',
            PARQUET_VERSION V{parquet_version},
            CODEC {escape(compression)},
            COMPRESSION_LEVEL {compression_level}
        );
        """
    )
