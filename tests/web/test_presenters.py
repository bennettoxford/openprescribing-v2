import pytest

from openprescribing.data.models import BNFCode
from openprescribing.web.presenters import make_bnf_table, make_bnf_tree


@pytest.mark.django_db(databases=["data"])
def test_make_bnf_tree(bnf_codes):
    codes = BNFCode.objects.filter(
        level__lte=BNFCode.Level.CHEMICAL_SUBSTANCE
    ).order_by("code")

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
