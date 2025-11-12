import textwrap

import duckdb
import responses
from responses.matchers import query_param_matcher

from openprescribing.data.fetchers import bnf_codes


@responses.activate
def test_bnf_codes_fetch(tmp_path):
    # Dataset index
    responses.get(
        "https://opendata.nhsbsa.net/api/3/action/package_show",
        match=[query_param_matcher({"id": "bnf-code-information-current-year"})],
        json={
            "result": {
                "resources": [
                    {
                        "name": "BNF_CODE_CURRENT_202509_VERSION_10",
                        "created": "2025-09-15T14:59:00.904819",
                        "last_modified": "2025-09-19T14:59:00.904819",
                        "url": "http://example.com/BNF_202509.csv",
                    },
                    {
                        "name": "BNF_CODE_CURRENT_202508_VERSION_9_FINAL",
                        "created": "2025-10-16T13:39:48.205150",
                        "last_modified": None,
                        "url": "http://example.com/BNF_202508.csv",
                    },
                ]
            },
        },
    )

    CSV_FILE = textwrap.dedent(
        """\
        BNF_CHAPTER,BNF_CHAPTER_CODE
        "Gastro-Intestinal System",01
        "Cardiovascular System",02
        """
    )
    responses.get(
        "http://example.com/BNF_202509.csv",
        body=CSV_FILE.encode("latin1"),
    )

    # Assume we've already downloaded this file
    bnf_codes_file = (
        tmp_path / "bnf_codes" / "bnf_codes_2025-08-01_v0009_2025-10-16T1339.parquet"
    )
    bnf_codes_file.parent.mkdir()
    bnf_codes_file.touch()

    bnf_codes.fetch(tmp_path)

    output_file = (
        tmp_path / "bnf_codes" / "bnf_codes_2025-09-01_v0010_2025-09-19T1459.parquet"
    )

    results = duckdb.read_parquet(str(output_file))
    assert results.columns == ["BNF_CHAPTER", "BNF_CHAPTER_CODE"]
    assert results.fetchall() == [
        ("Gastro-Intestinal System", "01"),
        ("Cardiovascular System", "02"),
    ]
