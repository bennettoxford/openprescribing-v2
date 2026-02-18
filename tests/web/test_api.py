import pytest

from openprescribing.web import api


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles(client, sample_data):
    rsp = client.get("/api/prescribing-deciles/?ntr_codes=1001030U0")
    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["deciles"][-1]["value"] == pytest.approx(64.15, 0.001)
    assert payload["org"] == []


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles_with_practice(client, sample_data):
    rsp = client.get("/api/prescribing-deciles/?ntr_codes=1001030U0&org_id=PRA00")
    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["deciles"][-1]["value"] == pytest.approx(66.41, 0.001)
    assert payload["org"][-1]["value"] == pytest.approx(51.94, 0.001)


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles_with_exclusion(client, sample_data):
    rsp = client.get("/api/prescribing-deciles/?ntr_codes=1001030U0,-1001030U0AAABAB")
    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["deciles"][-1]["value"] == pytest.approx(59.07, 0.001)
    assert payload["org"] == []


@pytest.mark.django_db(databases=["data"])
def test_prescribing_deciles_with_denominator(client, sample_data):
    rsp = client.get(
        "/api/prescribing-deciles/?ntr_codes=1001030U0AA&dtr_codes=1001030U0"
    )
    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["deciles"][-1]["value"] == pytest.approx(27.14, 0.001)
    assert payload["org"] == []


def test_nans_to_nones():
    records = [{"k1": 1.0, "k2": "aaa"}, {"k1": float("NaN"), "k2": "bbb"}]
    api.nans_to_nones(records)
    assert records == [{"k1": 1.0, "k2": "aaa"}, {"k1": None, "k2": "bbb"}]
