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
