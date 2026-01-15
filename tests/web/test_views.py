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
def test_multiple_bnf_search(client, sample_data):
    rsp = client.get("/bnf_codes/")
    assert rsp.status_code == 200

    rsp = client.get("/bnf_codes/?codes=1001030U0")
    assert rsp.status_code == 200
    assert "/api/prescribing-deciles/?codes=1001030U0" in rsp.text

    rsp = client.get("/bnf_codes/?codes=1001030U0AAABAB%0D%0A1001030U0AAABAB")
    assert rsp.status_code == 200
    assert "/api/prescribing-deciles/?codes=1001030U0AAABAB,1001030U0AAABAB" in rsp.text


@pytest.mark.xfail
@pytest.mark.django_db(databases=["data"])
def test_multiple_bnf_search_with_org(client, sample_data):
    rsp = client.get("/bnf_codes/?codes=1001030U0&org_id=PRA00")
    assert rsp.status_code == 200
    assert "/api/prescribing-deciles/?codes=1001030U0&org_id=PRA00" in rsp.text
