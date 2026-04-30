import pytest

from openprescribing.data.analysis import Analysis, AnalysisQuery
from openprescribing.data.bnf_query import BNFQuery, MultiBNFQuery, ProductType
from openprescribing.data.list_size_query import ListSizeQuery


def test_from_params():
    analysis = Analysis.from_params(
        {
            "ntr_bnf_codes": "01",
            "ntr_bnf_codes_excluded": "0101",
            "ntr_form_route_ids_excluded": "2",
            "ntr_vtm_ids": "5",
            "ntr_product_type": "generic",
            "dtr_bnf_codes": "01",
            "dtr_bnf_codes_excluded": "0101",
            "dtr_ingredient_ids_excluded": "4",
            "dtr_vtm_ids_excluded": "6",
            "dtr_product_type": "all",
            "org_id": "PRAC01",
        }
    )

    assert analysis.ntr_query == BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        product_type=ProductType.GENERIC,
        form_route_ids_excluded=["2"],
        vtm_ids=["5"],
    )
    assert analysis.dtr_query == BNFQuery(
        bnf_codes=["01"],
        bnf_codes_excluded=["0101"],
        ingredient_ids_excluded=["4"],
        vtm_ids_excluded=["6"],
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
        (
            AnalysisQuery(
                ntr_query=BNFQuery(
                    bnf_codes=["01"],
                    bnf_codes_excluded=["0101"],
                    product_type=ProductType.BRANDED,
                    form_route_ids_excluded=["2"],
                    vtm_ids=["5"],
                ),
                dtr_query=BNFQuery(
                    bnf_codes=["01"],
                    bnf_codes_excluded=["0101"],
                    ingredient_ids_excluded=["4"],
                    vtm_ids_excluded=["6"],
                ),
            ),
        ),
        org_id="PRAC01",
    )

    assert analysis.to_params() == {
        "ntr_bnf_codes": "01",
        "ntr_bnf_codes_excluded": "0101",
        "ntr_product_type": "branded",
        "ntr_form_route_ids_excluded": "2",
        "ntr_vtm_ids": "5",
        "dtr_bnf_codes": "01",
        "dtr_bnf_codes_excluded": "0101",
        "dtr_product_type": "all",
        "dtr_ingredient_ids_excluded": "4",
        "dtr_vtm_ids_excluded": "6",
        "org_id": "PRAC01",
    }


def test_to_params_dtr_list_size():
    analysis = Analysis(
        (
            AnalysisQuery(
                ntr_query=BNFQuery(
                    bnf_codes=["01"],
                    bnf_codes_excluded=["0101"],
                    product_type=ProductType.BRANDED,
                ),
                dtr_query=ListSizeQuery(),
            ),
        ),
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


def test_from_dict_multiple_queries(medications):
    medications.add_rows(
        [
            {"bnf_code": "1001030U0AAABAB", "ingredient_ids": [11111]},
            {"bnf_code": "1001030U0AAACAC", "ingredient_ids": [11111, 53034005]},
            {"bnf_code": "1001030U0BDAAAB", "ingredient_ids": [11111]},
            {"bnf_code": "1001030U0BDABAC", "ingredient_ids": [11111, 53034005]},
        ]
    )
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": {
                        "included": ["1001030U0"],
                    },
                    "product_type": "generic",
                },
            },
            {
                "numerator": {
                    "bnf_codes": {
                        "included": ["1001030U0"],
                    },
                    "product_type": "branded",
                },
            },
        ],
    }
    analysis = Analysis.from_dict(analysis_dict)
    # breakpoint()
    # query = BNFQuery(
    #     bnf_codes=["1001030U0"],
    #     ingredient_ids=["11111"],
    #     ingredient_ids_excluded=["53034005"],
    # )
    assert analysis.ntr_query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]

    assert analysis.to_dict() == analysis_dict


def test_from_dict_multiple_queries_dtr(medications):
    medications.add_rows(
        [
            # methotrexate
            {"bnf_code": "1001030U0AAABAB", "ingredient_ids": [11111]},
            {"bnf_code": "1001030U0AAACAC", "ingredient_ids": [11111, 53034005]},
            {"bnf_code": "1001030U0BDAAAB", "ingredient_ids": [11111]},
            {"bnf_code": "1001030U0BDABAC", "ingredient_ids": [11111, 53034005]},
            # leflunomide
            {"bnf_code": "1001030L0AAABAB", "ingredient_ids": [386981009]},
            {"bnf_code": "1001030L0AAACAC", "ingredient_ids": [386981009]},
            {"bnf_code": "1001030L0BDAAAB", "ingredient_ids": [386981009]},
            {"bnf_code": "1001030L0BDABAC", "ingredient_ids": [386981009]},
        ]
    )
    analysis_dict = {
        "queries": [
            {
                "numerator": {
                    "bnf_codes": {
                        "included": ["1001030U0_AB"],
                    },
                },
                "denominator": {
                    "bnf_codes": {
                        "included": ["1001030U0"],
                    },
                },
            },
            {
                "numerator": {
                    "bnf_codes": {
                        "included": ["1001030L0_AC"],
                    },
                },
                "denominator": {
                    "bnf_codes": {
                        "included": ["1001030L0"],
                    },
                },
            },
        ],
    }
    analysis = Analysis.from_dict(analysis_dict)

    assert isinstance(analysis.ntr_query, MultiBNFQuery)
    assert analysis.ntr_query.get_matching_presentation_codes() == [
        "1001030L0AAACAC",
        "1001030L0BDABAC",
        "1001030U0AAABAB",
        "1001030U0BDAAAB",
    ]
    assert analysis.dtr_query.get_matching_presentation_codes() == [
        "1001030L0AAABAB",
        "1001030L0AAACAC",
        "1001030L0BDAAAB",
        "1001030L0BDABAC",
        "1001030U0AAABAB",
        "1001030U0AAACAC",
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]

    assert analysis.to_dict() == analysis_dict
