import pytest

from openprescribing.data.bnf_query import BNFQuery, ProductType


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes(bnf_codes):
    query = BNFQuery.build(["1001030U0AA", "1001030U0BD", "-1001030U0AAABAB"], "all")
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_no_excludes(bnf_codes):
    query = BNFQuery.build(["1001030U0AA"], ProductType.ALL)
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_strength_and_formulation(bnf_codes):
    query = BNFQuery.build(["1001030U0_AC"], ProductType.ALL)
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAACAC",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_generic(bnf_codes):
    query = BNFQuery.build(["1001030U0"], ProductType.GENERIC)
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_generic_with_strength_and_formulation(
    bnf_codes,
):
    query = BNFQuery.build(["1001030U0_AB"], ProductType.GENERIC)
    assert query.get_matching_presentation_codes() == [
        "1001030U0AAABAB",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_branded(bnf_codes):
    query = BNFQuery.build(["1001030U0"], ProductType.BRANDED)
    assert query.get_matching_presentation_codes() == [
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_get_matching_presentation_codes_for_branded_with_strength_and_formulation(
    bnf_codes,
):
    query = BNFQuery.build(["1001030U0_AB"], ProductType.BRANDED)
    assert query.get_matching_presentation_codes() == [
        "1001030U0BDAAAB",
    ]


@pytest.mark.django_db(databases=["data"])
def test_describe_search_for_all_product_types(bnf_codes):
    query = BNFQuery.build(["1001030U0", "-1001030U0_AB"], ProductType.ALL)
    assert query.describe() == {
        "product_type": ProductType.ALL,
        "includes": [
            {
                "code": "1001030U0",
                "description": "Methotrexate",
            }
        ],
        "excludes": [
            {
                "code": "1001030U0_AB",
                "description": "Methotrexate 2.5mg tablets (branded and generic)",
            }
        ],
    }


@pytest.mark.django_db(databases=["data"])
def test_describe_search_for_generic_products(bnf_codes):
    query = BNFQuery.build(["1001030U0", "-1001030U0_AB"], ProductType.GENERIC)
    assert query.describe() == {
        "product_type": ProductType.GENERIC,
        "includes": [
            {
                "code": "1001030U0",
                "description": "Methotrexate",
            }
        ],
        "excludes": [
            {
                "code": "1001030U0_AB",
                "description": "Methotrexate 2.5mg tablets",
            }
        ],
    }


def test_from_params():
    query = BNFQuery.from_params(
        "ntr", {"ntr_codes": "01,-0101", "ntr_product_type": "generic"}
    )
    assert query == BNFQuery.build(["01", "-0101"], ProductType.GENERIC)


def test_to_params():
    query = BNFQuery.build(["01", "-0101"], ProductType.GENERIC)
    assert query.to_params("ntr") == {
        "ntr_codes": "01,-0101",
        "ntr_product_type": "generic",
    }
