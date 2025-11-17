import datetime

import duckdb
import responses

from openprescribing.data.fetchers import ods


@responses.activate
def test_ods_fetch(tmp_path, freezer):
    responses.post(
        "https://www.odsdatasearchandexport.nhs.uk/api/search/organisationReportSearch",
        json={
            # Note this is a very small subset of the fields we get in the real data
            "orgArray": [
                {
                    "id": "Y05381",
                    "name": "0-19 EAST CHESHIRE HEALTH VISITORS",
                    "inactive": False,
                    "country": "ENGLAND",
                    "role": ["RO247"],
                    "opStartDate": "2016-04-01",
                    "primaryRole": "RO177",
                    "primaryRoleName": "PRESCRIBING COST CENTRE",
                    "roleName": ["COMMUNITY HEALTH SERVICE PRESCRIBING COST CENTRE"],
                    "nonPrimaryRoleOpStartDates": ["2016-04-20"],
                },
            ],
        },
    )

    freezer.move_to("2025-11-15")

    ods.fetch(tmp_path)

    output_file = tmp_path / "ods" / "ods_2025-11-15.parquet"

    results = duckdb.read_parquet(str(output_file))
    assert results.columns == [
        "id",
        "name",
        "inactive",
        "country",
        "role",
        "opStartDate",
        "primaryRole",
        "primaryRoleName",
        "roleName",
        "nonPrimaryRoleOpStartDates",
    ]
    assert results.fetchall() == [
        (
            "Y05381",
            "0-19 EAST CHESHIRE HEALTH VISITORS",
            False,
            "ENGLAND",
            ["RO247"],
            datetime.date(2016, 4, 1),
            "RO177",
            "PRESCRIBING COST CENTRE",
            ["COMMUNITY HEALTH SERVICE PRESCRIBING COST CENTRE"],
            [datetime.date(2016, 4, 20)],
        )
    ]


@responses.activate
def test_ods_fetch_does_nothing_if_recently_fetched(tmp_path, freezer):
    output_file = tmp_path / "ods" / "ods_2025-11-15.parquet"
    output_file.parent.mkdir()
    output_file.touch()
    freezer.move_to("2025-11-15")
    ods.fetch(tmp_path)
    assert list(tmp_path.glob("ods/*")) == [output_file]


@responses.activate
def test_ods_fetch_refetches_if_not_recently_fetched(tmp_path, freezer):
    responses.post(
        "https://www.odsdatasearchandexport.nhs.uk/api/search/organisationReportSearch",
        json={"orgArray": []},
    )
    output_file = tmp_path / "ods" / "ods_2025-10-15.parquet"
    output_file.parent.mkdir()
    output_file.touch()
    freezer.move_to("2025-11-03")
    ods.fetch(tmp_path)
    assert (tmp_path / "ods" / "ods_2025-11-03.parquet").exists()
