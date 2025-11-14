import pytest

from openprescribing.data.models import BNFCode


@pytest.mark.django_db(databases=["data"])
def test_index(client):
    BNFCode.objects.create(code="0601023AW", name="Semaglutide", level=5)

    rsp = client.get("/")
    assert rsp.status_code == 200

    rsp = client.get("/?code=0601023AW")
    assert rsp.status_code == 200
