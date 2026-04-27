import pytest

from openprescribing.data.analysis import Analysis
from openprescribing.data.bnf_query import BNFQuery, ProductType
from openprescribing.data.list_size_query import ListSizeQuery


def test_from_params():
    analysis = Analysis.from_params(
        {
            "ntr_bnf_codes": "01",
            "ntr_bnf_codes_excluded": "0101",
            "ntr_form_route_ids_excluded": "2",
            "ntr_product_type": "generic",
            "dtr_bnf_codes": "01",
            "dtr_bnf_codes_excluded": "0101",
            "dtr_ingredient_ids_excluded": "4",
            "dtr_product_type": "all",
            "org_id": "PRAC01",
        }
    )

    assert analysis.ntr_query == BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        form_route_ids_excluded=["2"],
    )
    assert analysis.dtr_query == BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        ingredient_ids_excluded=["4"],
    )
    assert analysis.org_id == "PRAC01"


def test_from_params_ntr_codes_only():
    analysis = Analysis.from_params(
        {
            "ntr_bnf_codes": "01",
            "ntr_bnf_codes_excluded": "0101",
        }
    )

    assert analysis.ntr_query == BNFQuery(bnf_codes=["01"], bnf_codes_excluded=["0101"])
    assert analysis.dtr_query == ListSizeQuery()
    assert analysis.org_id is None


def test_to_params():
    analysis = Analysis(
        ntr_query=BNFQuery(
            bnf_codes=["01"],
            bnf_codes_excluded=["0101"],
            product_type=ProductType.BRANDED,
            form_route_ids_excluded=["2"],
        ),
        dtr_query=BNFQuery(
            bnf_codes=["01"],
            bnf_codes_excluded=["0101"],
            ingredient_ids_excluded=["4"],
        ),
        org_id="PRAC01",
    )

    assert analysis.to_params() == {
        "ntr_bnf_codes": "01",
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "branded",
        "ntr_form_route_ids_excluded": "2",
        "dtr_bnf_codes": "01",
        "dtr_bnf_codes_excluded": "0101",
        "dtr_product_type": "all",
        "dtr_ingredient_ids_excluded": "4",
        "org_id": "PRAC01",
    }


def test_to_params_dtr_list_size():
    analysis = Analysis(
        ntr_query=BNFQuery(
            bnf_codes=["01"],
            bnf_codes_excluded=["0101"],
            product_type=ProductType.BRANDED,
        ),
        dtr_query=ListSizeQuery(),
        org_id=None,
    )

    assert analysis.to_params() == {
        "ntr_bnf_codes": "01",
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "branded",
    }


@pytest.mark.django_db(databases=["data"])
def test_from_dict():
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": {
                        "included": ["01"],
                        "excluded": ["0101"],
                    },
                },
                "denominator": {
                    "bnf_codes": {
                        "included": ["01"],
                    }
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
        "queries": [
            {
                "numerator": {
                    "product_type": "branded",
                    "bnf_codes": {
                        "included": ["01"],
                        "excluded": ["0101"],
                    },
                },
                "denominator": {
                    "product_type": "branded",
                    "bnf_codes": {
                        "included": ["01"],
                    },
                },
            }
        ]
    }
    analysis = Analysis.from_dict(analysis_dict)
    assert analysis.to_dict() == analysis_dict


@pytest.mark.django_db(databases=["data"])
def test_from_dict_numerator_only():
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "product_type": "branded",
                    "bnf_codes": {
                        "included": ["01"],
                        "excluded": ["0101"],
                    },
                }
            }
        ]
    }
    analysis = Analysis.from_dict(analysis_dict)
    assert analysis.to_dict() == analysis_dict


@pytest.mark.django_db(databases=["data"])
def test_from_dict_ingredients():
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": {
                        "included": ["01"],
                    },
                    "ingredient_ids": ["01"],
                },
            }
        ],
    }
    analysis = Analysis.from_dict(analysis_dict)
    assert analysis.to_dict() == analysis_dict
