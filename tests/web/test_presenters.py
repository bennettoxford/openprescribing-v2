import pytest

from openprescribing.data.models import BNFCode
from openprescribing.web.presenters import make_bnf_table


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
        [
            [{"code": "1001030U0AAABAB", "name": "Methotrexate 2.5mg tablets"}],
            [{"code": "1001030U0BDAAAB", "name": "Maxtrex 2.5mg tablets"}],
        ],
        [
            [{"code": "1001030U0AAACAC", "name": "Methotrexate 10mg tablets"}],
            [{"code": "1001030U0BDABAC", "name": "Maxtrex 10mg tablets"}],
        ],
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
        [
            [
                {
                    "code": "0601060D0BSAAA0",
                    "name": "Prestige Smart System testing strips",
                }
            ],
        ],
    ]
