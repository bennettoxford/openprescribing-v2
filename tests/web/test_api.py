import pytest


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles(client, sample_data):
    rsp = client.get("/api/prescribing-deciles/?codes=1001030U0")
    assert rsp.status_code == 200


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles_with_practice(client, sample_data):
    rsp = client.get("/api/prescribing-deciles/?codes=1001030U0&org_id=PRA00")
    assert rsp.status_code == 200
