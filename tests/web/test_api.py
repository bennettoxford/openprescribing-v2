import json
from urllib.parse import urlencode

import pytest

from openprescribing.web import api
from tests.utils.ingest_utils import ingest_dmd_bnf_map_data, ingest_dmd_data


def _analysis_dict_to_param(analysis_dict):
    return urlencode({"analysis": json.dumps(analysis_dict)})


@pytest.mark.parametrize(
    "analysis_dict, expected_last_value",
    [
        (
            {
                "queries": [
                    {
                        "numerator": {
                            "bnf_codes": ["1001030U0"],
                        },
                    },
                ],
            },
            65.09,
        ),
        (
            {
                "queries": [
                    {
                        "numerator": {
                            "bnf_codes": ["1001030U0"],
                        },
                    },
                ],
                "org_id": "PRA00",
            },
            68.40,
        ),
        (
            {
                "queries": [
                    {
                        "numerator": {
                            "bnf_codes": ["1001030U0"],
                            "bnf_codes_excluded": ["1001030U0AAABAB"],
                        },
                    },
                ],
            },
            59.67,
        ),
        (
            {
                "queries": [
                    {
                        "numerator": {
                            "bnf_codes": ["1001030U0AA"],
                        },
                        "denominator": {
                            "bnf_codes": ["1001030U0"],
                        },
                    },
                ],
            },
            27.77,
        ),
    ],
)
def test_prescribing_all_orgs(client, sample_data, analysis_dict, expected_last_value):
    rsp = client.get(
        f"/api/prescribing-all-orgs/?{_analysis_dict_to_param(analysis_dict)}"
    )
    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["all_orgs"][-1]["value"] == pytest.approx(expected_last_value, 0.001)


def test_prescribing_deciles(client, sample_data):
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": ["1001030U0"],
                },
            },
        ],
    }
    rsp = client.get(
        f"/api/prescribing-deciles/?{_analysis_dict_to_param(analysis_dict)}"
    )

    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["deciles"][-1]["value"] == pytest.approx(64.15, 0.001)
    assert payload["org"] == []


def test_prescribing_deciles_with_practice(client, sample_data):
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": ["1001030U0"],
                },
            },
        ],
        "org_id": "PRA00",
    }
    rsp = client.get(
        f"/api/prescribing-deciles/?{_analysis_dict_to_param(analysis_dict)}"
    )

    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["deciles"][-1]["value"] == pytest.approx(66.41, 0.001)
    assert payload["org"][-1]["value"] == pytest.approx(51.94, 0.001)


def test_prescribing_deciles_with_exclusion(client, sample_data):
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": ["1001030U0"],
                    "bnf_codes_excluded": ["1001030U0AAABAB"],
                },
            },
        ],
    }
    rsp = client.get(
        f"/api/prescribing-deciles/?{_analysis_dict_to_param(analysis_dict)}"
    )

    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["deciles"][-1]["value"] == pytest.approx(59.07, 0.001)
    assert payload["org"] == []


def test_prescribing_deciles_with_denominator(client, sample_data):
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": ["1001030U0AA"],
                },
                "denominator": {
                    "bnf_codes": ["1001030U0"],
                },
            },
        ],
    }
    rsp = client.get(
        f"/api/prescribing-deciles/?{_analysis_dict_to_param(analysis_dict)}"
    )

    payload = rsp.json()
    assert rsp.status_code == 200
    assert payload["deciles"][-1]["value"] == pytest.approx(27.14, 0.001)
    assert payload["org"] == []


def test_prescribing_medications(client, sample_data):
    # The sample data has four presentations under 1001030U0, which is fewer than the
    # default top-N, so each is shown under its own name and there is no "Other" band.
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": ["1001030U0"],
                },
            },
        ],
    }
    rsp = client.get(
        f"/api/prescribing-medications/?{_analysis_dict_to_param(analysis_dict)}"
    )

    payload = rsp.json()
    assert rsp.status_code == 200
    medications = {record["medication"] for record in payload["medications"]}
    assert medications == {
        "Methotrexate 2.5mg tablets",
        "Methotrexate 10mg tablets",
        "Maxtrex 2.5mg tablets",
        "Maxtrex 10mg tablets",
    }


def test_prescribing_medications_groups_other(client, sample_data, monkeypatch):
    # With the top-N lowered below the number of matching presentations, the
    # lower-prescribing medications are summed into a single "Other" band.
    monkeypatch.setattr(api, "MEDICATIONS_TOP_N", 2)

    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": ["1001030U0"],
                },
            },
        ],
    }
    rsp = client.get(
        f"/api/prescribing-medications/?{_analysis_dict_to_param(analysis_dict)}"
    )

    payload = rsp.json()
    assert rsp.status_code == 200
    medications = {record["medication"] for record in payload["medications"]}
    # Two named medications plus "Other".
    assert len(medications) == 3
    assert "Other" in medications


def test_metadata_medications(client, rxdb, settings, tmp_path):
    rxdb.ingest([{"bnf_code": "1106000X0AAA4A4"}])
    ingest_dmd_data(settings, tmp_path)
    ingest_dmd_bnf_map_data(settings, tmp_path)
    rsp = client.get("/api/metadata/medications/")
    payload = rsp.json()

    assert {
        "id": 9393711000001102,
        "bnf_code": "1106000X0AAA4A4",
        "name": "Pilocarpine hydrochloride 6% eye drops preservative free (Special Order)",
        "is_amp": True,
        "vmp_id": 36016311000001102,
        "vtm_id": 90356005,
        "invalid": False,
        "form_routes": ["liquiddrops.ophthalmic"],
        "ingredient_ids": [387035001],
    } in payload["medications"]
    assert {
        "id": 36016311000001102,
        "bnf_code": "1106000X0AAA4A4",
        "name": "Pilocarpine hydrochloride 6% eye drops preservative free",
        "is_amp": False,
        "vmp_id": 36016311000001102,
        "vtm_id": 90356005,
        "invalid": False,
        "form_routes": ["liquiddrops.ophthalmic"],
        "ingredient_ids": [387035001],
    } in payload["medications"]


@pytest.mark.django_db(databases=["data"])
def test_metadata_dmd(client, settings, tmp_path):
    ingest_dmd_data(settings, tmp_path)
    rsp = client.get("/api/metadata/dmd/")
    payload = rsp.json()
    assert {
        "id": 108502004,
        "name": "Adenosine",
    } in payload["vtm"]
    assert {
        "id": 35894711000001106,
        "vtm_id": 108502004,
        "name": "Adenosine 6mg/2ml solution for injection vials",
    } in payload["vmp"]
    assert {
        "id": 4744411000001104,
        "vmp_id": 35894711000001106,
        "name": "Adenocor 6mg/2ml solution for injection vials (Sanofi)",
    } in payload["amp"]
    assert {
        "id": 35431001,
        "name": "Adenosine",
    } in payload["ingredient"]
    assert {"id": 24, "descr": "solutioninjection.intravenous"} in payload[
        "ont_form_route"
    ]


def test_metadata_bnf(client, bnf_codes):
    rsp = client.get("/api/metadata/bnf/")
    payload = rsp.json()
    assert {
        "code": "10",
        "level": 1,
        "name": "Musculoskeletal and Joint Diseases",
    } in payload["bnf"]
    assert {
        "code": "1001030U0",
        "level": 5,
        "name": "Methotrexate",
    } in payload["bnf"]
    assert {
        "code": "1001030U0_AB",
        "level": 6,
        "name": "Methotrexate 2.5mg tablets",
    } in payload["bnf"]
    assert {
        "code": "1001030U0BDAAAB",
        "level": 7,
        "name": "Maxtrex 2.5mg tablets",
    } in payload["bnf"]


def test_nans_to_nones():
    records = [{"k1": 1.0, "k2": "aaa"}, {"k1": float("NaN"), "k2": "bbb"}]
    api.nans_to_nones(records)
    assert records == [{"k1": 1.0, "k2": "aaa"}, {"k1": None, "k2": "bbb"}]
