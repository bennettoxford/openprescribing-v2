import pytest


def test_index(client):
    rsp = client.get("/")
    assert rsp.status_code == 200
    assert "Prescribing data over time for a single BNF Code" in rsp.content.decode(
        "utf-8"
    )


@pytest.mark.django_db(databases=["data"])
def test_bnf_search(client, sample_data):
    rsp = client.get("/bnf_code/")
    assert rsp.status_code == 200

    rsp = client.get("/bnf_code/?code=1001030U0")
    assert rsp.status_code == 200

    rsp = client.get("/bnf_code/?code=1001030U0&org_id=PRA00")
    assert rsp.status_code == 200


@pytest.mark.django_db(databases=["data"])
def test_multiple_bnf_search(client):
    BNFCode.objects.create(code="0601023AW", name="Semaglutide", level=5)
    Org.objects.create(id="PRAC05", name="Practice 5", org_type=Org.OrgType.PRACTICE)

    rsp = client.get("/bnf_codes/")
    assert rsp.status_code == 200

    rsp = client.get("/bnf_codes/?code=0601023AW")
    assert rsp.status_code == 200

    rsp = client.get("/bnf_codes/?code=0601023AW&org_id=PRAC05")
    assert rsp.status_code == 200
