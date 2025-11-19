import pytest

from openprescribing.data.models import BNFCode, Org


@pytest.mark.django_db(databases=["data"])
def test_index(client):
    BNFCode.objects.create(code="0601023AW", name="Semaglutide", level=5)
    Org.objects.create(id="PRAC05", name="Practice 5", org_type=Org.OrgType.PRACTICE)

    rsp = client.get("/")
    assert rsp.status_code == 200

    rsp = client.get("/?code=0601023AW")
    assert rsp.status_code == 200

    rsp = client.get("/?code=0601023AW&practice_id=PRAC05")
    assert rsp.status_code == 200
