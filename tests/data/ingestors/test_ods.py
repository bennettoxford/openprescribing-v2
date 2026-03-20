import pytest
from freezegun import freeze_time

from openprescribing.data.ingestors import ods
from openprescribing.data.models import Org
from tests.utils.parquet_utils import parquet_from_dicts


@pytest.mark.django_db(databases=["data"])
def test_ods_ingest(tmp_path, settings):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"
    data = [
        {
            "id": "Y61",
            "name": "EAST OF ENGLAND COMMISSIONING REGION",
            "inactive": False,
            "roleName": [],
            "primaryRoleName": "NHS ENGLAND (REGION)",
            "isPartnerToCode": [],
            "RE4": "",
            "ICB": "QUE",
            "NHSER": "Y61",
            "country": "ENGLAND",
        },
        {
            "id": "QHG",
            "name": "NHS BEDFORDSHIRE INTEGRATED CARE BOARD",
            "inactive": False,
            "roleName": ["INTEGRATED CARE BOARD"],
            "primaryRoleName": "STRATEGIC PARTNERSHIP",
            "isPartnerToCode": [],
            "RE4": "",
            "ICB": "QHG",
            "NHSER": "Y61",
            "country": "ENGLAND",
        },
        {
            "id": "M1J4Y",
            "name": "NHS BEDFORDSHIRE ICB - M1J4Y",
            "inactive": False,
            "roleName": ["SUB ICB LOCATION"],
            "primaryRoleName": "CLINICAL COMMISSIONING GROUP",
            "isPartnerToCode": [],
            "RE4": "",
            "ICB": "QHG",
            "NHSER": "Y61",
            "country": "ENGLAND",
        },
        {
            "id": "U49574",
            "name": "ASCENT PCN",
            "inactive": False,
            "roleName": [],
            "primaryRoleName": "PRIMARY CARE NETWORK",
            "isPartnerToCode": [],
            "RE4": "M1J4Y",
            "ICB": "QHG",
            "NHSER": "Y61",
            "country": "ENGLAND",
        },
        {
            "id": "E81050",
            "name": "ASPLANDS MEDICAL CENTRE",
            "inactive": False,
            "roleName": ["GP PRACTICE"],
            "primaryRoleName": "PRESCRIBING COST CENTRE",
            "isPartnerToCode": ["U49574"],
            "RE4": "M1J4Y",
            "ICB": "QHG",
            "NHSER": "Y61",
            "country": "ENGLAND",
        },
        {
            "id": "Y08176",
            "name": "ACHE PUTNOE BEDS",
            "inactive": False,
            "roleName": ["COMMUNITY HEALTH SERVICE PRESCRIBING COST CENTRE"],
            "primaryRoleName": "PRESCRIBING COST CENTRE",
            "isPartnerToCode": [],
            "RE4": "M1J4Y",
            "ICB": "QHG",
            "NHSER": "Y61",
            "country": "ENGLAND",
        },
        {
            "id": "W95633",
            "name": "74 MONK STREET",
            "inactive": False,
            "roleName": ["GP PRACTICE"],
            "primaryRoleName": "PRESCRIBING COST CENTRE",
            "isPartnerToCode": [],
            "RE4": "7A5",
            "ICB": "",
            "NHSER": "",
            "country": "WALES",
        },
    ]

    ods_file = settings.DOWNLOAD_DIR / "ods" / "ods.parquet"
    parquet_from_dicts(ods_file, data)

    ods.ingest()

    results = [
        (
            org.id,
            org.OrgType(org.org_type).name,
            org.name,
            {p.id for p in org.parents.all()},
        )
        for org in Org.objects.all()
    ]
    assert results == [
        (
            "ENGLAND",
            "NATION",
            "NHS England",
            set(),
        ),
        (
            "Y61",
            "REGION",
            "EAST OF ENGLAND COMMISSIONING REGION",
            {"ENGLAND"},
        ),
        (
            "QHG",
            "ICB",
            "NHS BEDFORDSHIRE INTEGRATED CARE BOARD",
            {"ENGLAND", "Y61"},
        ),
        (
            "M1J4Y",
            "SICBL",
            "NHS BEDFORDSHIRE ICB - M1J4Y",
            {"ENGLAND", "QHG", "Y61"},
        ),
        (
            "U49574",
            "PCN",
            "ASCENT PCN",
            {"ENGLAND", "QHG", "Y61", "M1J4Y"},
        ),
        (
            "E81050",
            "PRACTICE",
            "ASPLANDS MEDICAL CENTRE",
            {"ENGLAND", "Y61", "QHG", "U49574", "M1J4Y"},
        ),
        (
            "Y08176",
            "OTHER",
            "ACHE PUTNOE BEDS",
            {"ENGLAND", "QHG", "Y61", "M1J4Y"},
        ),
    ]

    # Attempting to re-ingest the same named file should do nothing. As a simple check for
    # this we empty the file contents and re-ingest. If the code does attempt to load it
    # then this will fail loudly.
    ods_file.write_text("")
    ods.ingest()


@pytest.mark.parametrize(
    "frozen_date,expected_pcn", [("2026-03-20", "U93165"), ("2026-04-20", "U25891")]
)
@pytest.mark.django_db(databases=["data"])
def test_ods_ingest_multiple_pcns(tmp_path, settings, frozen_date, expected_pcn):
    with freeze_time(frozen_date):
        settings.DOWNLOAD_DIR = tmp_path / "downloads"
        data = [
            {
                "id": "U93165",
                "name": "NORTH SOLIHULL PCN",
                "inactive": False,
                "roleName": [],
                "primaryRole": "RO272",
                "primaryRoleName": "PRIMARY CARE NETWORK",
                "isPartnerToCode": [],
                "RE4": "15E",
                "ICB": "QHL",
                "NHSER": "Y60",
                "country": "ENGLAND",
                "relationships": {
                    "PRESCRIBING COST CENTRE": [
                        {
                            "id": "726656",
                            "name": "ROWLANDS ROAD SURGERY",
                            "primaryRole": "RO177",
                            "role": ["RO177", "RO76"],
                            "primaryRoleName": "PRESCRIBING COST CENTRE",
                            "inactive": False,
                            "legEndDate": "2026-03-31",
                            "opStartDate": "2021-04-01",
                            "targetOrgRole": ["RO272"],
                            "sourceOrgRole": "RO76",
                            "relationshipTypeCode": "RE8",
                            "targetOrgCode": "U93165",
                            "legStartDate": "2021-04-01",
                            "sourceOrgCode": "M85171",
                            "opEndDate": "2026-03-31",
                            "status": "active",
                            "sourceOrgRoleName": "GP PRACTICE",
                        },
                    ]
                },
            },
            {
                "id": "U25891",
                "name": "SHELDON PCN",
                "inactive": False,
                "roleName": [],
                "primaryRole": "RO272",
                "primaryRoleName": "PRIMARY CARE NETWORK",
                "isPartnerToCode": [],
                "RE4": "15E",
                "ICB": "QHL",
                "NHSER": "Y60",
                "country": "ENGLAND",
                "relationships": {
                    "PRESCRIBING COST CENTRE": [
                        {
                            "id": "875109",
                            "name": "ROWLANDS ROAD SURGERY",
                            "primaryRole": "RO177",
                            "role": ["RO177", "RO76"],
                            "primaryRoleName": "PRESCRIBING COST CENTRE",
                            "nonPrimaryRoleName": ["GP PRACTICE"],
                            "inactive": True,
                            "opStartDate": "2026-04-01",
                            "relationshipTypeCode": "RE8",
                            "targetOrgCode": "U25891",
                            "legStartDate": "2026-04-01",
                            "targetOrgRole": ["RO272"],
                            "sourceOrgCode": "M85171",
                            "sourceOrgRole": "RO76",
                            "status": "retired",
                            "sourceOrgRoleName": "GP PRACTICE",
                            "legEndDate": "",
                            "lastChangeDate": "",
                            "opEndDate": "",
                        },
                    ]
                },
            },
            {
                "id": "M85171",
                "name": "ROWLANDS ROAD SURGERY",
                "inactive": False,
                "roleName": ["GP PRACTICE"],
                "primaryRole": "RO177",
                "primaryRoleName": "PRESCRIBING COST CENTRE",
                "isPartnerToCode": ["U36779", "U39721"],
                "RE4": "15E",
                "ICB": "QHL",
                "NHSER": "Y60",
                "country": "ENGLAND",
            },
        ]

        ods_file = settings.DOWNLOAD_DIR / "ods" / "ods.parquet"
        parquet_from_dicts(ods_file, data)

        org_types = [Org.OrgType.PCN, Org.OrgType.PRACTICE]
        ods.ingest(org_types=org_types)

        results = [
            (
                org.id,
                org.OrgType(org.org_type).name,
                org.name,
                {p.id for p in org.parents.all()},
            )
            for org in Org.objects.all()
        ]
        assert results == [
            ("ENGLAND", "NATION", "NHS England", set()),
            ("U93165", "PCN", "NORTH SOLIHULL PCN", {"ENGLAND"}),
            ("U25891", "PCN", "SHELDON PCN", {"ENGLAND"}),
            ("M85171", "PRACTICE", "ROWLANDS ROAD SURGERY", {"ENGLAND", expected_pcn}),
        ]


@freeze_time("2026-03-20")
@pytest.mark.django_db(databases=["data"])
def test_ods_ingest_multiple_pcns_missing_opEndDate(tmp_path, settings):
    settings.DOWNLOAD_DIR = tmp_path / "downloads"
    data = [
        {
            "id": "U39721",
            "name": "HILLS, BROOKS & DALES GROUP PCN",
            "inactive": False,
            "roleName": [],
            "primaryRole": "RO272",
            "primaryRoleName": "PRIMARY CARE NETWORK",
            "isPartnerToCode": [],
            "RE4": "72Q",
            "ICB": "QKK",
            "NHSER": "Y56",
            "country": "ENGLAND",
            "relationships": {
                "PRESCRIBING COST CENTRE": [
                    {
                        "id": "793254",
                        "name": "ONE CARE LAMBETH",
                        "primaryRole": "RO177",
                        "role": ["RO177", "RO76"],
                        "primaryRoleName": "PRESCRIBING COST CENTRE",
                        "inactive": False,
                        "opStartDate": "2021-05-01",
                        "relationshipTypeCode": "RE8",
                        "targetOrgCode": "U39721",
                        "legStartDate": "2021-05-01",
                        "targetOrgRole": ["RO272"],
                        "sourceOrgCode": "Y07020",
                        "sourceOrgRole": "RO76",
                        "status": "active",
                        "sourceOrgRoleName": "GP PRACTICE",
                        "legEndDate": "",
                        "lastChangeDate": "",
                        "opEndDate": "",
                    }
                ]
            },
        },
        {
            "id": "U36779",
            "name": "BRIXTON AND CLAPHAM PARK PCN",
            "inactive": False,
            "roleName": [],
            "primaryRole": "RO272",
            "primaryRoleName": "PRIMARY CARE NETWORK",
            "isPartnerToCode": [],
            "RE4": "72Q",
            "ICB": "QKK",
            "NHSER": "Y56",
            "country": "ENGLAND",
            "relationships": {
                "PRESCRIBING COST CENTRE": [
                    {
                        "id": "875081",
                        "name": "ONE CARE LAMBETH",
                        "primaryRole": "RO177",
                        "role": ["RO177", "RO76"],
                        "primaryRoleName": "PRESCRIBING COST CENTRE",
                        "inactive": False,
                        "opStartDate": "2026-03-15",
                        "relationshipTypeCode": "RE8",
                        "targetOrgCode": "U36779",
                        "legStartDate": "2026-03-15",
                        "targetOrgRole": ["RO272"],
                        "sourceOrgCode": "Y07020",
                        "sourceOrgRole": "RO76",
                        "status": "active",
                        "sourceOrgRoleName": "GP PRACTICE",
                        "legEndDate": "",
                        "lastChangeDate": "",
                        "opEndDate": "",
                    }
                ]
            },
        },
        {
            "id": "Y07020",
            "name": "ONE CARE LAMBETH",
            "inactive": False,
            "roleName": ["GP PRACTICE"],
            "primaryRole": "RO177",
            "primaryRoleName": "PRESCRIBING COST CENTRE",
            "isPartnerToCode": ["U36779", "U39721"],
            "RE4": "72Q",
            "ICB": "QKK",
            "NHSER": "Y56",
            "country": "ENGLAND",
        },
    ]

    ods_file = settings.DOWNLOAD_DIR / "ods" / "ods.parquet"
    parquet_from_dicts(ods_file, data)

    org_types = [Org.OrgType.PCN, Org.OrgType.PRACTICE]
    ods.ingest(org_types=org_types)

    results = [
        (
            org.id,
            org.OrgType(org.org_type).name,
            org.name,
            {p.id for p in org.parents.all()},
        )
        for org in Org.objects.all()
    ]
    assert results == [
        ("ENGLAND", "NATION", "NHS England", set()),
        ("U39721", "PCN", "HILLS, BROOKS & DALES GROUP PCN", {"ENGLAND"}),
        ("U36779", "PCN", "BRIXTON AND CLAPHAM PARK PCN", {"ENGLAND"}),
        ("Y07020", "PRACTICE", "ONE CARE LAMBETH", {"ENGLAND", "U36779"}),
    ]
