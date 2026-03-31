import io
import zipfile
from pathlib import Path

import duckdb
import responses

from openprescribing.data.fetchers import dmd


@responses.activate
def test_dmd_fetch(settings, tmp_path):
    settings.TRUD_API_KEY = "trud_api_key"
    responses.get(
        "https://isd.digital.nhs.uk/trud/api/v1/keys/trud_api_key/items/24/releases?latest",
        json={
            "apiVersion": "1",
            "releases": [
                {
                    "id": "nhsbsa_dmd_3.4.0_20260330000001.zip",
                    "releaseDate": "2026-03-30",
                    "archiveFileUrl": "https://archive.file.url",
                }
            ],
            "httpStatus": 200,
            "message": "OK",
        },
    )
    responses.get(
        "https://archive.file.url",
        body=create_zip_archive_from_directory(Path("tests/fixtures/dmd")),
    )

    dmd.fetch(tmp_path)

    vtm_file = tmp_path / "dmd" / "dmd_2026-03-30_3.4.0_20260330000001" / "vtm.parquet"
    results = duckdb.read_parquet(str(vtm_file))
    assert results.columns == [
        "vtmid",
        "invalid",
        "nm",
        "abbrevnm",
        "vtmidprev",
        "vtmiddt",
    ]
    assert results.fetchall() == [
        ("108502004", None, "Adenosine", None, None, None),
        ("15219611000001105", None, "Coal tar + Salicylic acid", None, None, None),
        ("32889211000001103", None, "Diclofenac diethylammonium", None, None, None),
        ("90356005", None, "Pilocarpine", None, None, None),
    ]


@responses.activate
def test_dmd_fetch_when_already_fetched(settings, tmp_path):
    settings.TRUD_API_KEY = "trud_api_key"
    responses.get(
        "https://isd.digital.nhs.uk/trud/api/v1/keys/trud_api_key/items/24/releases?latest",
        json={
            "apiVersion": "1",
            "releases": [
                {
                    "id": "nhsbsa_dmd_3.4.0_20260330000001.zip",
                    "releaseDate": "2026-03-30",
                    "archiveFileUrl": "https://archive.file.url",
                }
            ],
            "httpStatus": 200,
            "message": "OK",
        },
    )

    release_dir = tmp_path / "dmd" / "dmd_2026-03-30_3.4.0_20260330000001"
    release_dir.mkdir(parents=True)

    dmd.fetch(tmp_path)

    assert not any(
        call.request.url == "https://archive.file.url" for call in responses.calls
    )


def create_zip_archive_from_directory(directory):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as zf:
        for path in directory.iterdir():
            zf.writestr(path.name, path.read_bytes())
    return buffer.getvalue()
