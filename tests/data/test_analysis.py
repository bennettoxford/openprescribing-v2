from openprescribing.data.analysis import Analysis
from openprescribing.data.bnf_query import BNFQuery, ProductType
from openprescribing.data.list_size_query import ListSizeQuery


def test_from_params():
    analysis = Analysis.from_params(
        {
            "ntr_codes": "01,-0101",
            "ntr_product_type": "generic",
            "dtr_codes": "01,-0101",
            "dtr_product_type": "all",
            "org_id": "PRAC01",
        }
    )

    assert analysis.ntr_query == BNFQuery.build(["01", "-0101"], ProductType.GENERIC)
    assert analysis.dtr_query == BNFQuery.build(["01", "-0101"], ProductType.ALL)
    assert analysis.org_id == "PRAC01"


def test_from_params_ntr_codes_only():
    analysis = Analysis.from_params(
        {
            "ntr_codes": "01,-0101",
        }
    )

    assert analysis.ntr_query == BNFQuery.build(["01", "-0101"], ProductType.ALL)
    assert analysis.dtr_query == ListSizeQuery()
    assert analysis.org_id is None


def test_to_params():
    analysis = Analysis(
        ntr_query=BNFQuery.build(["01", "-0101"], ProductType.BRANDED),
        dtr_query=BNFQuery.build(["01", "-0101"], ProductType.ALL),
        org_id="PRAC01",
    )

    assert analysis.to_params() == {
        "ntr_codes": "01,-0101",
        "ntr_product_type": "branded",
        "dtr_codes": "01,-0101",
        "dtr_product_type": "all",
        "org_id": "PRAC01",
    }


def test_to_params_dtr_list_size():
    analysis = Analysis(
        ntr_query=BNFQuery.build(["01", "-0101"], ProductType.BRANDED),
        dtr_query=ListSizeQuery(),
        org_id=None,
    )

    assert analysis.to_params() == {
        "ntr_codes": "01,-0101",
        "ntr_product_type": "branded",
    }


def test_from_dict():
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
                    "bnf_codes": {
                        "included": ["01"],
                        "excluded": ["0101"],
                    }
                },
            }
        ]
    }
    analysis = Analysis.from_dict(analysis_dict)
    assert analysis.to_params() == {
        "ntr_codes": "01,-0101",
        "ntr_product_type": "branded",
        "dtr_codes": "01,-0101",
        "dtr_product_type": "all",
    }


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
    assert analysis.to_params() == {
        "ntr_codes": "01,-0101",
        "ntr_product_type": "branded",
    }
