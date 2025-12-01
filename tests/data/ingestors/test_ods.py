import pytest

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
