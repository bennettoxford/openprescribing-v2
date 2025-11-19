import io
import textwrap
import zipfile
from datetime import date

import duckdb
import responses

from openprescribing.data.fetchers import list_size
from openprescribing.data.utils.html_utils import Resource


@responses.activate
def test_list_size_fetch(tmp_path, monkeypatch):
    responses.get(
        "https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice/",
        body="<div>content goes here</div>",
    )

    def mock_parse(html, heading_re):
        assert html == b"<div>content goes here</div>"
        return [
            Resource(
                url="/lists-jan-2017/",
                date=date(2017, 1, 1),
                published_date=date(2017, 1, 15),
            ),
            Resource(
                url="/lists-jan-2025/",
                date=date(2025, 1, 1),
                published_date=date(2025, 1, 15),
            ),
            Resource(
                url="/lists-feb-2025/",
                date=date(2025, 2, 1),
                published_date=date(2025, 2, 15),
            ),
        ]

    # This is tested separately, for our purposes here we just want a fixed list of
    # resources given some expected HTML
    monkeypatch.setattr(list_size, "parse_nhsd_callout_boxes", mock_parse)

    CSV_FILE = textwrap.dedent(
        """\
        practice_code,practice_name,value
        ABC123,"North Street",14
        DEF456,"Éclair",25
        """
    )

    # This month's data published as CSV
    responses.get(
        "https://digital.nhs.uk/lists-jan-2025/",
        body="<a href='2025-01/gp-reg-pat-prac-quin-age.csv'></a>",
    )
    responses.get(
        "https://digital.nhs.uk/2025-01/gp-reg-pat-prac-quin-age.csv",
        body=CSV_FILE.encode("latin1"),
    )

    # And this month's data published as ZIP
    responses.get(
        "https://digital.nhs.uk/lists-feb-2025/",
        body="<a href='2025-02/gp-reg-pat-prac-quin-age.zip'></a>",
    )
    responses.get(
        "https://digital.nhs.uk/2025-02/gp-reg-pat-prac-quin-age.zip",
        body=create_zip_archive(
            {"file.csv": CSV_FILE.encode("latin1")},
        ),
    )

    # Assume we've already downloaded this file
    list_size_file = (
        tmp_path / "list_size" / "list_size_2017-01-01_v1_2017-01-15.parquet"
    )
    list_size_file.parent.mkdir()
    list_size_file.touch()

    list_size.fetch(tmp_path)

    for name in [
        "list_size_2025-01-01_v2_2025-01-15.parquet",
        "list_size_2025-02-01_v2_2025-02-15.parquet",
    ]:
        path = tmp_path / "list_size" / name
        results = duckdb.read_parquet(str(path))
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
