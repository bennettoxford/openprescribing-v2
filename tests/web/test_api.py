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


@pytest.mark.django_db(databases=["data"])
def test_reshape_matrix(cdm):
    obs_records = list(api.reshape_matrix(cdm, row_name="centile", col_name="month"))
    rows = [
        ["2025-01-01", 10, 2.0],
        ["2025-01-01", 20, 4.0],
        ["2025-01-01", 30, 6.0],
        ["2025-01-01", 40, 8.0],
        ["2025-01-01", 50, 10.0],
        ["2025-01-01", 60, 12.0],
        ["2025-01-01", 70, 14.0],
        ["2025-01-01", 80, 16.0],
        ["2025-01-01", 90, 18.0],
        ["2025-02-01", 10, 3.0],
        ["2025-02-01", 20, 5.0],
        ["2025-02-01", 30, 7.0],
        ["2025-02-01", 40, 9.0],
        ["2025-02-01", 50, 11.0],
        ["2025-02-01", 60, 13.0],
        ["2025-02-01", 70, 15.0],
        ["2025-02-01", 80, 17.0],
        ["2025-02-01", 90, 19.0],
    ]
    exp_records = [dict(zip(["month", "centile", "value"], row)) for row in rows]
    assert obs_records == exp_records


@pytest.mark.django_db(databases=["data"])
@pytest.mark.parametrize(
    "params, expected_last_value",
    [
        ("?ntr_codes=1001030U0", 65.09),
        ("?ntr_codes=1001030U0&org_id=PRA00", 68.40),
        ("?ntr_codes=1001030U0,-1001030U0AAABAB", 59.67),
        ("?ntr_codes=1001030U0AA&dtr_codes=1001030U0", 27.77),
    ],
)
def test_prescribing_all_orgs(client, sample_data, params, expected_last_value):
    rsp = client.get(f"/api/prescribing-all-orgs/{params}")
    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["all_orgs"][-1]["value"] == pytest.approx(expected_last_value, 0.001)


def test_nans_to_nones():
    records = [{"k1": 1.0, "k2": "aaa"}, {"k1": float("NaN"), "k2": "bbb"}]
    api.nans_to_nones(records)
    assert records == [{"k1": 1.0, "k2": "aaa"}, {"k1": None, "k2": "bbb"}]
