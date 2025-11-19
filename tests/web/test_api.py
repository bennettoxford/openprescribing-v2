import pytest

from openprescribing.data.models import BNFCode, Org


@pytest.mark.django_db(databases=["data"])
def test_prescribing(client, rxdb):
    BNFCode.objects.create(code="0601023AW", name="Semaglutide", level=5)
    Org.objects.create(id="PRAC05", name="Practice 5", org_type=Org.OrgType.PRACTICE)
    rxdb.ingest(
        [
            {"bnf_code": "0601023AWAAAEAE", "practice_code": "PRAC05", "items": 10},
        ]
    )

    rsp = client.get("/api/prescribing/?code=0601023AW")
    assert rsp.status_code == 200
