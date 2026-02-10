import json

import pytest


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles(client, sample_data):
    rsp = client.get("/api/prescribing-deciles/?ntr_codes=1001030U0")
    assert rsp.status_code == 200
    assert (
        next(iter(json.loads(rsp.text)["datasets"].values()))[-1]["value"]
        == 64.15611215168303
    )


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles_with_practice(client, sample_data):
    rsp = client.get("/api/prescribing-deciles/?ntr_codes=1001030U0&org_id=PRA00")
    assert rsp.status_code == 200


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles_with_exclusion(client, sample_data):
    rsp = client.get("/api/prescribing-deciles/?ntr_codes=1001030U0,-1001030U0AAABAB")
    assert rsp.status_code == 200
    assert next(iter(json.loads(rsp.text)["datasets"].values()))[-1][
        "value"
    ] == pytest.approx(59.07, 0.001)


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles_with_denominator(client, sample_data):
    rsp = client.get(
        "/api/prescribing-deciles/?ntr_codes=1001030U0AA&dtr_codes=1001030U0"
    )
    assert rsp.status_code == 200
