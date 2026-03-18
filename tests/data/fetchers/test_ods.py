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
def test_ods_fetch_with_pcn_relationships(tmp_path, freezer):
    responses.post(
        "https://www.odsdatasearchandexport.nhs.uk/api/search/organisationReportSearch",
        json={
            # Note this is a very small subset of the fields we get in the real data
            "orgArray": [
                {
                    "id": "M84059",
                    "name": "SPA MEDICAL CENTRE",
                    "inactive": False,
                    "country": "ENGLAND",
                    "role": ["RO76"],
                    "opStartDate": "1974-04-01",
                    "primaryRole": "RO177",
                    "RE8": ["U36452", "U82789"],
                    "legStartDate": "1974-04-01",
                    "primaryRoleName": "PRESCRIBING COST CENTRE",
                    "roleName": ["GP PRACTICE"],
                    "isPartnerToName": ["LEAMINGTON NORTH PCN", "LEAMINGTON SOUTH PCN"],
                    "isPartnerToPrimaryRoleName": [
                        "PRIMARY CARE NETWORK",
                        "PRIMARY CARE NETWORK",
                    ],
                    "isPartnerToLegalStartDate": ["2019-10-01"],
                    "isPartnerToLegalEndDate": ["2026-03-31"],
                    "isPartnerToCode": ["U82789", "U36452"],
                },
                {
                    "id": "U36452",
                    "name": "LEAMINGTON SOUTH PCN",
                    "inactive": False,
                    "country": "ENGLAND",
                    "legEndDate": "2026-03-31",
                    "role": [],
                    "opStartDate": "2019-10-01",
                    "primaryRole": "RO272",
                    "opEndDate": "2026-03-31",
                    "legStartDate": "2019-10-01",
                    "primaryRoleName": "PRIMARY CARE NETWORK",
                    "isPartnerToName": [],
                    "isPartnerToPrimaryRoleName": [],
                    "isPartnerToLegalStartDate": [],
                    "isPartnerToLegalEndDate": [],
                    "isPartnerToCode": [],
                },
            ],
        },
    )

    responses.get(
        "https://www.odsdatasearchandexport.nhs.uk/api/search/singleOrganisationSearchByCode?code=U36452",
        json={
            "main": {
                "id": "U36452",
                "name": "LEAMINGTON SOUTH PCN",
                "inactive": False,
                "country": "ENGLAND",
                "legEndDate": "2026-03-31",
                "role": [],
                "opStartDate": "2019-10-01",
                "primaryRole": "RO272",
                "opEndDate": "2026-03-31",
                "legStartDate": "2019-10-01",
                "primaryRoleName": "PRIMARY CARE NETWORK",
                "isPartnerToName": [],
                "isPartnerToPrimaryRoleName": [],
                "isPartnerToLegalStartDate": [],
                "isPartnerToLegalEndDate": [],
                "isPartnerToCode": [],
            },
            "relationships": {
                "PRESCRIBING COST CENTRE": [
                    {
                        "id": "613222",
                        "name": "SPA MEDICAL CENTRE",
                        "primaryRole": "RO177",
                        "role": ["RO177", "RO76"],
                        "town": "LEAMINGTON SPA",
                        "address1": "81 RADFORD ROAD",
                        "postcode": "CV31 1NE",
                        "primaryRoleName": "PRESCRIBING COST CENTRE",
                        "nonPrimaryRoleName": ["GP PRACTICE"],
                        "inactive": False,
                        "legEndDate": "2026-03-31",
                        "opStartDate": "2019-10-01",
                        "targetOrgRole": ["RO272"],
                        "sourceOrgRole": "RO76",
                        "relationshipTypeCode": "RE8",
                        "targetOrgCode": "U36452",
                        "legStartDate": "2019-10-01",
                        "sourceOrgCode": "M84059",
                        "opEndDate": "2026-03-31",
                        "status": "active",
                        "sourceOrgRoleName": "GP PRACTICE",
                        "lastChangeDate": "",
                    }
                ]
            },
            "predecessor": None,
            "successor": None,
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
        "RE8",
        "legStartDate",
        "primaryRoleName",
        "roleName",
        "isPartnerToName",
        "isPartnerToPrimaryRoleName",
        "isPartnerToLegalStartDate",
        "isPartnerToLegalEndDate",
        "isPartnerToCode",
        "legEndDate",
        "opEndDate",
        "relationships",
    ]
    assert results.fetchall() == [
        (
            "M84059",
            "SPA MEDICAL CENTRE",
            False,
            "ENGLAND",
            ["RO76"],
            datetime.date(1974, 4, 1),
            "RO177",
            ["U36452", "U82789"],
            datetime.date(1974, 4, 1),
            "PRESCRIBING COST CENTRE",
            ["GP PRACTICE"],
            ["LEAMINGTON NORTH PCN", "LEAMINGTON SOUTH PCN"],
            ["PRIMARY CARE NETWORK", "PRIMARY CARE NETWORK"],
            [datetime.date(2019, 10, 1)],
            [datetime.date(2026, 3, 31)],
            ["U82789", "U36452"],
            None,
            None,
            None,
        ),
        (
            "U36452",
            "LEAMINGTON SOUTH PCN",
            False,
            "ENGLAND",
            [],
            datetime.date(2019, 10, 1),
            "RO272",
            None,
            datetime.date(2019, 10, 1),
            "PRIMARY CARE NETWORK",
            None,
            [],
            [],
            [],
            [],
            [],
            datetime.date(2026, 3, 31),
            datetime.date(2026, 3, 31),
            {
                "PRESCRIBING COST CENTRE": [
                    {
                        "id": "613222",
                        "name": "SPA MEDICAL CENTRE",
                        "primaryRole": "RO177",
                        "role": ["RO177", "RO76"],
                        "town": "LEAMINGTON SPA",
                        "address1": "81 RADFORD ROAD",
                        "postcode": "CV31 1NE",
                        "primaryRoleName": "PRESCRIBING COST CENTRE",
                        "nonPrimaryRoleName": ["GP PRACTICE"],
                        "inactive": False,
                        "legEndDate": datetime.date(2026, 3, 31),
                        "opStartDate": datetime.date(2019, 10, 1),
                        "targetOrgRole": ["RO272"],
                        "sourceOrgRole": "RO76",
                        "relationshipTypeCode": "RE8",
                        "targetOrgCode": "U36452",
                        "legStartDate": datetime.date(2019, 10, 1),
                        "sourceOrgCode": "M84059",
                        "opEndDate": datetime.date(2026, 3, 31),
                        "status": "active",
                        "sourceOrgRoleName": "GP PRACTICE",
                        "lastChangeDate": "",
                    }
                ]
            },
        ),
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
