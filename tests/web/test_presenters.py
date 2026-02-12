import pytest

from openprescribing.data.models import BNFCode
from openprescribing.web.presenters import (
    make_bnf_table,
    make_bnf_tree,
    make_code_to_name,
    make_ntr_dtr_intersection_table,
)


@pytest.mark.django_db(databases=["data"])
def test_make_bnf_tree(bnf_codes):
    codes = BNFCode.objects.all()

    assert make_bnf_tree(codes) == [
        {
            "code": "06",
            "name": "Endocrine System",
            "children": [
                {
                    "code": "0601",
                    "name": "Drugs used in diabetes",
                    "children": [
                        {
                            "code": "060106",
                            "name": "Diabetic diagnostic and monitoring agents",
                            "children": [
                                {
                                    "code": "0601060",
                                    "name": "Diabetic diagnostic and monitoring agents",
                                    "children": [
                                        {
                                            "code": "0601060D0",
                                            "name": "Glucose blood testing reagents",
                                            "children": [],
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "code": "10",
            "name": "Musculoskeletal and Joint Diseases",
            "children": [
                {
                    "code": "1001",
                    "name": "Drugs used in rheumatic diseases and gout",
                    "children": [
                        {
                            "code": "100103",
                            "name": "Rheumatic disease suppressant drugs",
                            "children": [
                                {
                                    "code": "1001030",
                                    "name": "Rheumatic disease suppressant drugs",
                                    "children": [
                                        {
                                            "code": "1001030U0",
                                            "name": "Methotrexate",
                                            "children": [],
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ],
        },
    ]


@pytest.mark.django_db(databases=["data"])
def test_make_bnf_table_with_generic_products(bnf_codes):
    code = "1001030U0"
    products = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRODUCT
    ).order_by("code")
    presentations = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRESENTATION
    ).order_by("code")

    headers, rows = make_bnf_table(products, presentations)

    assert headers == [
        {"code": "1001030U0AA", "name": "Methotrexate (Rheumatism)"},
        {"code": "1001030U0BD", "name": "Maxtrex (Rheumatism)"},
    ]
    assert rows == [
        {
            "code": "1001030U0_AB",
            "cells": [
                [{"code": "1001030U0AAABAB", "name": "Methotrexate 2.5mg tablets"}],
                [{"code": "1001030U0BDAAAB", "name": "Maxtrex 2.5mg tablets"}],
            ],
        },
        {
            "code": "1001030U0_AC",
            "cells": [
                [{"code": "1001030U0AAACAC", "name": "Methotrexate 10mg tablets"}],
                [{"code": "1001030U0BDABAC", "name": "Maxtrex 10mg tablets"}],
            ],
        },
    ]


@pytest.mark.django_db(databases=["data"])
def test_make_bnf_table_with_no_generic_products(bnf_codes):
    code = "0601060D0"
    products = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRODUCT
    ).order_by("code")
    presentations = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRESENTATION
    ).order_by("code")

    headers, rows = make_bnf_table(products, presentations)

    assert headers == [
        {"code": "0601060D0BS", "name": "Prestige"},
    ]
    assert rows == [
        {
            "code": None,
            "cells": [
                [
                    {
                        "code": "0601060D0BSAAA0",
                        "name": "Prestige Smart System testing strips",
                    }
                ],
            ],
        }
    ]


@pytest.mark.parametrize(
    "ntr_codes, ntr_product_type, dtr_codes, dtr_product_type, expected",
    [
        (
            ["1001030U0AAABAB"],
            "all",
            ["1001030U0AAABAB", "1001030U0BDAAAB"],
            "all",
            {
                "has_denominators": True,
                "data": [
                    ("1001030U0AAABAB", "Methotrexate 2.5mg tablets", True, True),
                    ("1001030U0BDAAAB", "Maxtrex 2.5mg tablets", False, True),
                ],
            },
        ),
        (
            ["1001030U0AAABAB"],
            "all",
            None,
            None,
            {
                "has_denominators": False,
                "data": [
                    ("1001030U0AAABAB", "Methotrexate 2.5mg tablets", True, None),
                ],
            },
        ),
        (
            ["1001030U0AAABAB", "1001030U0BDAAAB"],
            "all",
            ["1001030U0AA", "-1001030U0AAACAC"],
            "all",
            {
                "has_denominators": True,
                "data": [
                    ("1001030U0AAABAB", "Methotrexate 2.5mg tablets", True, True),
                    ("1001030U0BDAAAB", "Maxtrex 2.5mg tablets", True, False),
                ],
            },
        ),
        (
            ["1001030U0AAABAB"],
            "all",
            ["1001030U0"],
            "generic",
            {
                "has_denominators": True,
                "data": [
                    ("1001030U0AAABAB", "Methotrexate 2.5mg tablets", True, True),
                    ("1001030U0AAACAC", "Methotrexate 10mg tablets", False, True),
                ],
            },
        ),
        (
            ["1001030U0"],
            "generic",
            ["1001030U0"],
            "all",
            {
                "has_denominators": True,
                "data": [
                    ("1001030U0AAABAB", "Methotrexate 2.5mg tablets", True, True),
                    ("1001030U0AAACAC", "Methotrexate 10mg tablets", True, True),
                    ("1001030U0BDAAAB", "Maxtrex 2.5mg tablets", False, True),
                    ("1001030U0BDABAC", "Maxtrex 10mg tablets", False, True),
                ],
            },
        ),
    ],
)
@pytest.mark.django_db(databases=["data"])
def test_make_ntr_dtr_intersection_table(
    bnf_codes, ntr_codes, ntr_product_type, dtr_codes, dtr_product_type, expected
):
    actual = make_ntr_dtr_intersection_table(
        ntr_codes, ntr_product_type, dtr_codes, dtr_product_type
    )

    # verify expected namedtuple keys exist
    assert actual["data"][0].code == expected["data"][0][0]
    assert actual["data"][0].name == expected["data"][0][1]
    assert actual["data"][0].ntr == expected["data"][0][2]
    assert actual["data"][0].dtr == expected["data"][0][3]

    # verify all contents
    assert actual["data"] == expected["data"]

    assert actual["has_denominators"] is expected["has_denominators"]


@pytest.mark.django_db(databases=["data"])
def test_make_code_to_name(bnf_codes):
    codes = BNFCode.objects.filter(code__startswith="10")
    assert make_code_to_name(codes) == {
        "10": "Musculoskeletal and Joint Diseases",
        "1001": "Drugs used in rheumatic diseases and gout",
        "100103": "Rheumatic disease suppressant drugs",
        "1001030": "Rheumatic disease suppressant drugs",
        "1001030U0": "Methotrexate",
        "1001030U0_AB": "Methotrexate 2.5mg tablets (branded and generic)",
        "1001030U0_AC": "Methotrexate 10mg tablets (branded and generic)",
    }
