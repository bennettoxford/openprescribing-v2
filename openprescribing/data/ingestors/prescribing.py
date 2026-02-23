import logging

import duckdb
from django.conf import settings

from openprescribing.data.utils.duckdb_utils import escape
from openprescribing.data.utils.filename_utils import (
    get_latest_files_by_date,
    get_temp_filename_for,
)


log = logging.getLogger(__name__)


def ingest(force=False):
    target_file = settings.PRESCRIBING_DATABASE
    prescribing_files = get_latest_files_by_date(
        settings.DOWNLOAD_DIR.glob("prescribing/*")
    )
    list_size_files = get_latest_files_by_date(
        # We only ingest version 2 files at present
        settings.DOWNLOAD_DIR.glob("list_size/*_v2_*")
    )

    # List sizes are published on a different schedule from prescribing data, but we
    # only care about files corresponding to periods for which we have prescribing data
    list_size_files = {
        date: filename
        for date, filename in list_size_files.items()
        if date in prescribing_files
    }

    all_files = sorted([*prescribing_files.values(), *list_size_files.values()])

    conn = duckdb.connect()

    if not force and target_file.exists():
        conn.sql(f"ATTACH {escape(target_file)} AS old (READONLY)")
        ingested_files = {
            f["filename"]
            for f in fetch_as_dicts(conn, "SELECT * FROM old.ingested_file")
        }
    else:
        ingested_files = set()

    if {f.name for f in all_files} == ingested_files:
        log.debug("No new data to ingest")
        return

    for filename in all_files:
        log.info(f"Preparing to ingest file: {filename.name}")

    # Attach the file we're in the process of building under the schema name "new". The
    # STORAGE_VERSION setting allows us to opt-in to newer DuckDB file format features
    # which can't be read by older clients. If a newer release offers a feature we want
    # we can bump the version here.
    target_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = get_temp_filename_for(target_file)
    conn.sql(f"ATTACH {escape(tmp_file)} AS new (STORAGE_VERSION 'v1.2.0')")

    # Record the names of the files we're ingesting
    conn.sql("CREATE TABLE new.ingested_file (filename TEXT)")
    conn.executemany(
        "INSERT INTO new.ingested_file VALUES (?)",
        [(f.name,) for f in all_files],
    )

    # Create views over all our source files, presenting each group of files as if they
    # were a single table. We then query these views to build the rest of the tables.
    conn.sql(
        "CREATE TEMPORARY VIEW prescribing_source AS "
        + sql_for_prescribing_source_view(
            prescribing_files,
        )
    )
    conn.sql(
        "CREATE TEMPORARY VIEW list_size_source AS "
        + sql_for_list_size_source_view(
            list_size_files,
        )
    )
    conn.sql(
        "CREATE TEMPORARY VIEW bnf_code_changes_source AS "
        + sql_for_bnf_code_changes_view(
            settings.BNF_CODE_CHANGES_DIR / "bnf_code_mapping.csv"
        )
    )

    # Set the new database we're building as the default schema
    conn.sql("USE new")

    # Ingest all the data by querying the source views and writing the results to tables
    ingest_sources(conn)

    conn.close()
    tmp_file.replace(target_file)


def sql_for_prescribing_source_view(prescribing_files_by_date):
    # Return a query which reads from the supplied files and converts them into a
    # single, unified consistent structure ready for us to build from

    # We start by creating a query to read from each individual file
    subqueries = [
        f"""
        SELECT
            -- We know the relevant date for each file so we add it as fixed column
            {escape(date)}::DATE AS date,
            -- Map an inconsistently named column to something consistent
            COLUMNS('(BNF_CODE|BNF_PRESENTATION_CODE)') AS our_bnf_code,
            *
        FROM read_parquet({escape(filename)})
        """
        for date, filename in prescribing_files_by_date.items()
    ]
    # We combine these all into a single table (columns which are not present in a given
    # file will just have NULL values)
    combined = " UNION ALL BY NAME ".join(subqueries)

    # Read from the above union, map the column names to the ones we want to use and
    # where necessary apply transformations
    return f"""\
    SELECT
        our_bnf_code AS bnf_code,
        -- Not every file has SNOMED codes so we use zero as a placeholder
        COALESCE(CAST(SNOMED_CODE AS INT8), 0) AS snomed_code,
        date AS date,
        PRACTICE_CODE AS practice_code,
        QUANTITY AS quantity_value,
        ITEMS AS items,
        TOTAL_QUANTITY AS quantity,
        -- We want prices in pence not pounds so we can use integers later
        CAST(NIC AS DOUBLE) * 100 AS net_cost,
        CAST(ACTUAL_COST AS DOUBLE) * 100 AS actual_cost
    FROM
        ({combined})
    """


def sql_for_list_size_source_view(list_size_files_by_date):
    # Return a query which reads from the supplied files and converts them into a
    # single, unified consistent structure ready for us to build from

    # We start by creating a query to read from each individual file
    subqueries = [
        f"""
        SELECT
            -- We know the relevant date for each file so we add it as fixed column
            {escape(date)}::DATE AS date,
            *
        FROM read_parquet({escape(filename)})
        """
        for date, filename in list_size_files_by_date.items()
    ]
    # We combine these all into a single table (columns which are not present in a given
    # file will just have NULL values)
    combined = " UNION ALL BY NAME ".join(subqueries)

    # Read from the above union, extracting just the value we're currently interested in
    return f"""\
    SELECT
        date AS date,
        ORG_CODE AS practice_code,
        NUMBER_OF_PATIENTS AS total
    FROM
        ({combined})
    WHERE
        ORG_TYPE = 'GP' AND SEX = 'ALL' AND AGE_GROUP_5 = 'ALL'
    """


def ingest_sources(conn):
    log.info("Building `date` table")
    conn.sql("CREATE TABLE date AS " + sql_for_date_table())
    log.info(f"Ingested {count_table(conn, 'date'):,} dates")

    log.info("Building `practice` table")
    conn.sql("CREATE TABLE practice AS " + sql_for_practice_table())
    log.info(f"Ingested {count_table(conn, 'practice'):,} practices")

    log.info("Building `presentation` table")
    conn.sql("CREATE TABLE presentation AS " + sql_for_presentation_table())
    log.info(f"Ingested {count_table(conn, 'presentation'):,} presentations")

    log.info("Building `list_size_norm` table")
    conn.sql("CREATE TABLE list_size_norm AS " + sql_for_list_size_normalised())
    log.info(f"Ingested {count_table(conn, 'list_size_norm'):,} list size rows")

    # We store the prescribing data in a fully normalised table ("prescribing_norm") so
    # that date and practice and presentation (bnf and snomed code) are stored as
    # integer foreign keys to other tables. This is crucial to getting the performance
    # we need out of DuckDB.
    #
    # The types below are chosen to be as small as possible while still being able to
    # represent the range of values we need. If ever we exceed these (e.g. we try to
    # ingest more than 256 months of data) then the ingest will fail loudly. We can then
    # decide whether to ingest less, or to change the type here and pay the extra cost
    # in storage and performance. Nothing else in the system depends on these exact
    # types though, so it shouldn't be a disruptive change.
    conn.sql(
        """
        CREATE TABLE prescribing_norm (
            presentation_id INT4,
            date_id UTINYINT,
            practice_id USMALLINT,
            quantity_value FLOAT4,
            items USMALLINT,
            quantity FLOAT4,
            net_cost UINTEGER,
            actual_cost UINTEGER
        )
        """
    )

    # The order in which we insert the normalised prescribing data is important because
    # it allows DuckDB to produce more useful zonemaps, which improves query performance.
    # We want data primarily ordered by `presentation_id` as that's what we most
    # frequently query on and it's also the highest cardinality column (i.e. querying on
    # it allows us to quickly discard a large proportion of the data). After that,
    # `date_id` is the next most important as we will sometimes limit our queries by
    # date. Finally we order by `practice_id`; we rarely query on this but it's better to
    # have the data ordered than not.
    #
    # Due to the size of the prescribing data we can't just issue a single query to
    # fetch, sort and insert the data: DuckDB ends up spilling to disk while doing the
    # sort which makes the whole process grind to a (near) halt. However, we can exploit
    # the fact that presentations are ordered by BNF code and so we can process the data
    # in smaller chunks by filtering on ranges of BNF codes. As long as we process these
    # ranges in order, and as long as we correctly order the data in each chunk, then
    # the overall table ends up correctly ordered as well.
    #
    # This also relies on the fact that filtering the incoming data by BNF code is
    # relatively cheap. If these were CSV files we'd need to do a full scan over all the
    # data every time. But thanks the magic of Parquet these queries are reasonably
    # efficient.
    for bnf_start, bnf_end in get_bnf_code_ranges(conn, batch_size=750):
        log.info(f"Building `prescribing_norm` table: {bnf_start} -> {bnf_end}")
        conn.sql(
            "INSERT INTO prescribing_norm "
            + sql_for_prescribing_normalised()
            + " WHERE prescribing_source.bnf_code >= ? AND prescribing_source.bnf_code < ?"
            + " ORDER BY presentation_id, date_id, practice_id",
            params=[bnf_start, bnf_end],
        )

    log.info(f"Ingested {count_table(conn, 'prescribing_norm'):,} prescribing rows")

    # To make ad-hoc queries of the data easier we create denormalised views which
    # include the practice codes, dates etc rather than just foreign keys
    log.info("Building `prescribing` view")
    conn.sql("CREATE VIEW prescribing AS " + sql_for_prescribing_denormalised())

    log.info("Building `list_size` view")
    conn.sql("CREATE VIEW list_size AS " + sql_for_list_size_denormalised())

    # To support BNF codes changing we need to update the presentation table with the
    # BNF code that a presentation would have, if it had been prescribed today.  We
    # keep the original in the original_bnf_code column for debugging purposes.
    log.info("Updating `presentation` table")
    conn.sql("""
    CREATE OR REPLACE TABLE presentation AS
    SELECT
        presentation.id,
        COALESCE(bnf_code_changes_source.new_code, presentation.bnf_code) AS bnf_code,
        presentation.bnf_code AS original_bnf_code,
        presentation.snomed_code
    FROM presentation
    LEFT JOIN bnf_code_changes_source
        ON presentation.bnf_code = bnf_code_changes_source.old_code
    """)


def sql_for_date_table():
    # Return a series of all unique dates present in the prescribing data together with
    # an integer ID.
    #
    # A couple of oddities here:
    #
    #  1. We start the IDs at 0 rather than 1 because we're going to use them as column
    #     indexes in a matrix and these are zero-indexed.
    #
    #  2. We sort the dates in descending order. When we filter by date we generally
    #     want to filter to just the more recent dates. By using a descending order this
    #     translates into filtering out date IDs larger than a certain value. And this
    #     means we don't have to allocate columns for these date IDs when building a
    #     results matrix. And this means we don't pay a cost for having historical data
    #     in the database unless we're actually querying it.
    #
    # Nothing will break if we don't do these things; we'll just waste memory and CPU
    # time.
    return """\
    SELECT
        CAST(
            (row_number() OVER (ORDER BY date DESC)) - 1
            AS UTINYINT)
        AS id,
        date
    FROM (
        SELECT DISTINCT date FROM prescribing_source
    )
    """


def sql_for_practice_table():
    # Return a series of all unique practice codes in the prescribing data together with
    # an integer ID.
    #
    # A couple of oddities here:
    #
    #  1. We start the IDs at 0 rather than 1 because we're going to use them as row
    #     indexes in a matrix and these are zero-indexed.
    #
    #  2. We sort practices by the date they last prescribed in descending order. This
    #     means that if we're only interested in prescribing after, say, January 2025
    #     then we can ignore all practices that haven't prescribed since December 2024
    #     and this will translate into ignoring all practices with IDs greater than,
    #     say, 1234. This means we don't have to allocate rows for these practices when
    #     building a results matrix. And this means we don't pay a cost for having
    #     historical data in the database unless we're actually querying it.
    #
    # Nothing will break if we don't do these things; we'll just waste memory and CPU
    # time.
    return """\
    SELECT
        CAST(
            (row_number() OVER (ORDER BY max_date DESC, practice_code)) - 1
            AS USMALLINT)
        AS id,
        practice_code AS code,
        max_date AS latest_prescribing_date
    FROM (
        SELECT MAX(date) AS max_date, practice_code
        FROM prescribing_source
        WHERE practice_code != '-'
        GROUP BY practice_code
    )
    """


def sql_for_presentation_table():
    # Return a series of all unqiue presentations in the prescribing data (by which we
    # mean all <BNF code, SNOMED code> pairs) together with an integer ID.
    #
    # We order by BNF code first because the hierarchical nature of BNF codes means that
    # clinically associated codes get lexically clustered together. And then, because we
    # order the entire prescribing dataset by presentation ID, related prescribing data
    # ends up clustered together on disk. This isn't essential for query performance,
    # but given that it's going to ordered by _something_ this is the most sensible
    # option.
    return """\
    SELECT
        CAST(
            (row_number() OVER (ORDER BY bnf_code, snomed_code))
            AS INT4)
        AS id,
        bnf_code,
        snomed_code
    FROM (
        SELECT DISTINCT bnf_code, snomed_code FROM prescribing_source
    )
    """


def sql_for_prescribing_normalised():
    return """\
    SELECT
        presentation.id AS presentation_id,
        date.id AS date_id,
        practice.id AS practice_id,
        prescribing_source.quantity_value,
        prescribing_source.items,
        prescribing_source.quantity,
        prescribing_source.net_cost,
        prescribing_source.actual_cost
    FROM
        prescribing_source
    JOIN
        presentation
    ON
        prescribing_source.bnf_code = presentation.bnf_code
        AND prescribing_source.snomed_code = presentation.snomed_code
    JOIN
        date ON prescribing_source.date = date.date
    JOIN
        practice ON prescribing_source.practice_code = practice.code
    """


def sql_for_prescribing_denormalised():
    return """\
    SELECT
        rx.presentation_id AS presentation_id,
        presentation.bnf_code AS bnf_code,
        presentation.snomed_code AS snomed_code,
        rx.date_id AS date_id,
        date.date AS date,
        rx.practice_id AS practice_id,
        practice.code AS practice_code,
        rx.quantity_value AS quantity_value,
        rx.items AS items,
        rx.quantity AS quantity,
        rx.net_cost AS net_cost,
        rx.actual_cost AS actual_cost
    FROM
        prescribing_norm AS rx
    JOIN
        presentation
    ON
        rx.presentation_id = presentation.id
    JOIN
        date
    ON
        rx.date_id = date.id
    JOIN
        practice
    ON
        rx.practice_id = practice.id
    """


def sql_for_list_size_normalised():
    return """\
    SELECT
        date.id AS date_id,
        practice.id AS practice_id,
        CAST(list_size_source.total AS UINTEGER) AS total
    FROM
        list_size_source
    JOIN
        date ON list_size_source.date = date.date
    JOIN
        practice ON list_size_source.practice_code = practice.code
    ORDER BY
        date_id, practice_id
    """


def sql_for_list_size_denormalised():
    return """\
    SELECT
        lst.date_id AS date_id,
        date.date AS date,
        lst.practice_id AS practice_id,
        practice.code AS practice_code,
        lst.total AS total
    FROM
        list_size_norm AS lst
    JOIN
        date
    ON
        lst.date_id = date.id
    JOIN
        practice
    ON
        lst.practice_id = practice.id
    """


def sql_for_bnf_code_changes_view(csv_path):
    # Return a query that reads data about BNF code changes.
    #
    # This data comes from a CSV file that maps all old codes to their equivalent code
    # today.

    return f"""\
    SELECT old_code, new_code
    FROM
        read_csv(
            {escape(csv_path)},
            header=True,
            columns={{
                'old_code': 'VARCHAR',
                'new_code': 'VARCHAR',
            }}
        )
    """


def get_bnf_code_ranges(conn, batch_size):
    query = conn.sql("SELECT DISTINCT bnf_code FROM presentation ORDER BY bnf_code")
    bnf_codes = [row[0] for row in query.fetchall()]
    for i in range(0, len(bnf_codes), batch_size):
        next_i = i + batch_size
        min_code = bnf_codes[i]
        # We need some end value which is guaranteed larger than any valid BNF code
        max_code = bnf_codes[next_i] if next_i < len(bnf_codes) else "ZZZZZZZZZZZZZZZ"
        yield min_code, max_code


def fetch_as_dicts(conn, query):
    cursor = conn.execute(query)
    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def count_table(conn, table):
    return conn.sql(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
