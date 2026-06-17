import pytest

from openprescribing.data.analysis import Analysis


@pytest.mark.django_db(databases=["data"])
def test_from_dict():
    analysis_dict = {
        "options": {
            "type": "prescribing_vs_prescribing",
            "output_value": "items",
        },
        "queries": [
            {
                "numerator": {
                    "bnf_codes": ["01"],
                    "bnf_codes_excluded": ["0101"],
                },
                "denominator": {
                    "bnf_codes": ["01"],
                },
            }
        ],
        "org_id": "PRAC01",
    }
    analysis = Analysis.from_dict(analysis_dict)
    assert analysis.to_dict() == analysis_dict


@pytest.mark.django_db(databases=["data"])
def test_from_dict_branded():
    analysis_dict = {
        "options": {
            "type": "prescribing_vs_prescribing",
            "output_value": "items",
        },
        "queries": [
            {
                "numerator": {
                    "product_type": "branded",
                    "bnf_codes": ["01"],
                    "bnf_codes_excluded": ["0101"],
                },
                "denominator": {
                    "product_type": "branded",
                    "bnf_codes": ["01"],
                },
            }
        ],
    }
    analysis = Analysis.from_dict(analysis_dict)
    assert analysis.to_dict() == analysis_dict


@pytest.mark.django_db(databases=["data"])
def test_from_dict_numerator_only():
    analysis_dict = {
        "options": {
            "type": "prescribing_vs_list_size",
            "output_value": "items",
        },
        "queries": [
            {
                "numerator": {
                    "product_type": "branded",
                    "bnf_codes": ["01"],
                    "bnf_codes_excluded": ["0101"],
                }
            }
        ],
    }
    analysis = Analysis.from_dict(analysis_dict)
    assert analysis.to_dict() == analysis_dict


@pytest.mark.django_db(databases=["data"])
def test_from_dict_ingredients():
    analysis_dict = {
        "options": {
            "type": "prescribing_vs_list_size",
            "output_value": "items",
        },
        "queries": [
            {
                "numerator": {
                    "bnf_codes": ["01"],
                    "ingredient_ids": [1],
                },
            }
        ],
    }
    analysis = Analysis.from_dict(analysis_dict)
    assert analysis.to_dict() == analysis_dict
