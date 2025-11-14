# We expect this will get covered when we add a prescribing_db fixture
# pragma: no cover file
import pytest

from openprescribing.data.models import BNFCode


@pytest.mark.xfail(reason="missing prescribing_db fixture")
@pytest.mark.django_db(databases=["data"])
def test_prescribing(client):
    BNFCode.objects.create(code="0601023AW", name="Semaglutide", level=5)

    rsp = client.get("/api/prescribing/?code=0601023AW")
    assert rsp.status_code == 200
