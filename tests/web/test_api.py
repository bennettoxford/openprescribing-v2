import pytest

from openprescribing.data.models import BNFCode, Org


@pytest.mark.django_db(databases=["data"])
def test_prescribing(client, rxdb):
    BNFCode.objects.create(code="0601023AW", name="Semaglutide", level=5)
    Org.objects.create(id="PRAC05", name="Practice 5", org_type=Org.OrgType.PRACTICE)
    rxdb.ingest(
        prescribing_data=[
            {"bnf_code": "0601023AWAAAEAE", "practice_code": "PRAC05", "items": 10},
        ],
        list_size_data=[
            {"practice_code": "PRAC05", "total": 20},
        ],
    )

    rsp = client.get("/api/prescribing/?code=0601023AW")
    assert rsp.status_code == 200


@pytest.mark.django_db(databases=["data"])
def test_prescribing_with_practice(client, rxdb):
    BNFCode.objects.create(code="0601023AW", name="Semaglutide", level=5)
    Org.objects.create(id="PRAC05", name="Practice 5", org_type=Org.OrgType.PRACTICE)
    rxdb.ingest(
        [
            {"bnf_code": "0601023AWAAAEAE", "practice_code": "PRAC05", "items": 10},
        ],
        list_size_data=[
            {"practice_code": "PRAC05", "total": 20},
        ],
    )

    rsp = client.get("/api/prescribing/?code=0601023AW&org_id=PRAC05")
    assert rsp.status_code == 200
