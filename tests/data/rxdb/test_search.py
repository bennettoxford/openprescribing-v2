import pytest

from openprescribing.data.rxdb.search import (
    ProductType,
    bnf_code_names,
    describe_search,
    search,
)


@pytest.mark.django_db(databases=["data"])
def test_search(bnf_codes):
    assert search(
        ["1001030U0AA", "1001030U0BD", "-1001030U0AAABAB"], ProductType.ALL
    ) == [
        "1001030U0AAACAC",
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_search_no_excludes(bnf_codes):
    assert search(["1001030U0AA"], ProductType.ALL) == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_search_for_strength_and_formulation(bnf_codes):
    assert search(["1001030U0_AC"], ProductType.ALL) == [
        "1001030U0AAACAC",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_search_for_generic(bnf_codes):
    assert search(["1001030U0"], ProductType.GENERIC) == [
        "1001030U0AAABAB",
        "1001030U0AAACAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_search_for_generic_with_strength_and_formulation(bnf_codes):
    assert search(["1001030U0_AB"], ProductType.GENERIC) == [
        "1001030U0AAABAB",
    ]


@pytest.mark.django_db(databases=["data"])
def test_search_for_branded(bnf_codes):
    assert search(["1001030U0"], ProductType.BRANDED) == [
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_search_for_branded_with_strength_and_formulation(bnf_codes):
    assert search(["1001030U0_AB"], ProductType.BRANDED) == [
        "1001030U0BDAAAB",
    ]


@pytest.mark.django_db(databases=["data"])
def test_describe_search_for_all_product_types(bnf_codes):
    assert describe_search(["1001030U0", "-1001030U0_AB"], ProductType.ALL) == {
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
    assert describe_search(["1001030U0", "-1001030U0_AB"], ProductType.GENERIC) == {
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


@pytest.mark.django_db(databases=["data"])
def test_bnf_code_names(bnf_codes):
    expected = {
        "1001030U0AAABAB": "Methotrexate 2.5mg tablets",
        "1001030U0AAACAC": "Methotrexate 10mg tablets",
        "1001030U0BDAAAB": "Maxtrex 2.5mg tablets",
        "1001030U0BDABAC": "Maxtrex 10mg tablets",
    }

    actual = bnf_code_names(
        ["1001030U0AAABAB", "1001030U0AAACAC", "1001030U0BDAAAB", "1001030U0BDABAC"]
    )
    assert actual == expected
