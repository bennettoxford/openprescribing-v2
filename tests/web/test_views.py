import pytest


def test_index(client):
    rsp = client.get("/")
    assert rsp.status_code == 200
    assert "Prescribing data over time for a single BNF Code" in rsp.text


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

    rsp = client.get("/bnf_codes/?ntr_codes=1001030U0")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_api_url"]
        == "/api/prescribing-deciles/?ntr_codes=1001030U0&ntr_product_type=all"
    )

    rsp = client.get("/bnf_codes/?ntr_codes=1001030U0&dtr_codes=1001")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_api_url"]
        == "/api/prescribing-deciles/?ntr_codes=1001030U0&ntr_product_type=all&dtr_codes=1001&dtr_product_type=all"
    )

    rsp = client.get("/bnf_codes/?ntr_codes=1001030U0AAABAB%0D%0A1001030U0AAABAB")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_api_url"]
        == "/api/prescribing-deciles/?ntr_codes=1001030U0AAABAB,1001030U0AAABAB&ntr_product_type=all"
    )

    rsp = client.get("/bnf_codes/?ntr_codes=1001030U0AA%0D%0A-1001030U0AAABAB")
    assert rsp.status_code == 200
    assert (
        rsp.context["prescribing_api_url"]
        == "/api/prescribing-deciles/?ntr_codes=1001030U0AA,-1001030U0AAABAB&ntr_product_type=all"
    )


@pytest.mark.django_db(databases=["data"])
def test_bnf_tree(client, bnf_codes):
    rsp = client.get("/bnf/")
    assert rsp.status_code == 200


@pytest.mark.django_db(databases=["data"])
def test_bnf_table_with_generic_products(client, bnf_codes):
    rsp = client.get("/bnf/1001030U0/")
    assert rsp.status_code == 200


@pytest.mark.django_db(databases=["data"])
def test_bnf_table_with_no_generic_products(client, bnf_codes):
    rsp = client.get("/bnf/0601060D0/")
    assert rsp.status_code == 200
