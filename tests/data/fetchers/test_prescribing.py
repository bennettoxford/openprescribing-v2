import io
import textwrap
import zipfile

import duckdb
import responses
from responses.matchers import query_param_matcher

from openprescribing.data.fetchers import prescribing


@responses.activate
def test_prescribing_fetch(tmp_path):
    # Dataset indexes
    responses.get(
        "https://opendata.nhsbsa.net/api/3/action/package_show",
        match=[
            query_param_matcher(
                {"id": "english-prescribing-dataset-epd-with-snomed-code"}
            )
        ],
        json={
            "result": {
                "resources": [
                    {
                        "id": "file-1",
                        "name": "EPD_SNOMED_202507",
                        "created": "2025-09-15T14:59:00.904819",
                        "last_modified": "2025-09-19T14:59:00.904819",
                    },
                    {
                        "id": "file-2",
                        "name": "EPD_SNOMED_202508",
                        "created": "2025-10-16T13:39:48.205150",
                        "last_modified": None,
                    },
                ]
            },
        },
    )
    responses.get(
        "https://opendata.nhsbsa.net/api/3/action/package_show",
        match=[query_param_matcher({"id": "english-prescribing-data-epd"})],
        json={
            "result": {
                "resources": [
                    {
                        "id": "file-3",
                        "name": "EPD_202001",
                        "created": "2020-03-04T12:13:14.000000",
                        "last_modified": None,
                    },
                ]
            },
        },
    )

    # Pointer to ZIP file for single resource
    responses.get(
        "https://opendata.nhsbsa.net/api/3/action/resource_show",
        match=[query_param_matcher({"id": "file-2"})],
        json={
            "result": {
                "zip_url": "https://abc.eu.r2.cloudflarestorage.com/EPD_SNOMED_202508.ZIP",
            },
        },
    )

    # ZIP file containing CSV
    CSV_FILE = textwrap.dedent(
        """\
        practice_code,practice_name,value
        ABC123,"North Street",14
        DEF456,"Éclair",25
        """
    )
    responses.get(
        "https://abc.eu.r2.cloudflarestorage.com/EPD_SNOMED_202508.ZIP",
        body=create_zip_archive(
            {"file.csv": CSV_FILE.encode("latin1")},
        ),
    )

    # Assume we've already downloaded these files
    prescribing_dir = tmp_path / "prescribing"
    prescribing_dir.mkdir()
    (prescribing_dir / "prescribing_2025-07-01_v3_2025-09-19T1459.parquet").touch()
    (prescribing_dir / "prescribing_2020-01-01_v2_2020-03-04T1213.parquet").touch()

    prescribing.fetch(tmp_path)

    output_file = (
        tmp_path / "prescribing" / "prescribing_2025-08-01_v3_2025-10-16T1339.parquet"
    )

    results = duckdb.read_parquet(str(output_file))
    assert results.columns == ["practice_code", "practice_name", "value"]
    assert results.fetchall() == [
        ("ABC123", "North Street", "14"),
        # Use an accented character so we can check Latin-1 encoding is handled
        # correctly
        ("DEF456", "Éclair", "25"),
    ]


def create_zip_archive(files):
    f = io.BytesIO()
    zf = zipfile.ZipFile(f, mode="w")
    for name, body in files.items():
        zf.writestr(name, body)
    zf.close()
    return f.getvalue()
