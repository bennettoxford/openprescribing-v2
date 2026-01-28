import pytest

from openprescribing.data.models import BNFCode
from openprescribing.data.models.bnf_codes import Parts


@pytest.mark.django_db(databases=["data"])
def test_parts(bnf_codes):
    assert bnf_code("10").parts == Parts(
        chapter="10",
        section=None,
        paragraph=None,
        subparagraph=None,
        chemical_substance=None,
        product=None,
        strength_and_formulation=None,
        generic_equivalent=None,
    )

    assert bnf_code("1001030U0BDABAC").parts == Parts(
        chapter="10",
        section="01",
        paragraph="03",
        subparagraph="0",
        chemical_substance="U0",
        product="BD",
        strength_and_formulation="AB",
        generic_equivalent="AC",
    )


@pytest.mark.django_db(databases=["data"])
def test_is_generic(bnf_codes):
    assert bnf_code("1001030U0AA").is_generic()
    assert not bnf_code("1001030U0BD").is_generic()
    assert bnf_code("1001030U0AAABAB").is_generic()
    assert not bnf_code("1001030U0BDAAAB").is_generic()


@pytest.mark.django_db(databases=["data"])
def test_is_ancestor_of(bnf_codes):
    assert bnf_code("1001").is_ancestor_of(bnf_code("100103"))
    assert bnf_code("1001030U0").is_ancestor_of(bnf_code("1001030U0AA"))
    assert bnf_code("1001030U0AA").is_ancestor_of(bnf_code("1001030U0AAABAB"))
    assert not bnf_code("1001030U0AA").is_ancestor_of(bnf_code("1001030U0BDAAAB"))
    assert not bnf_code("1001030U0AA").is_ancestor_of(bnf_code("1001030U0AA"))


@pytest.mark.django_db(databases=["data"])
def test_is_generic_equivalent_of(bnf_codes):
    assert bnf_code("1001030U0AAABAB").is_generic_equivalent_of(
        bnf_code("1001030U0BDAAAB")
    )
    assert not bnf_code("1001030U0AAABAB").is_generic_equivalent_of(
        bnf_code("1001030U0BDABAC")
    )


def bnf_code(code):
    return BNFCode.objects.get(code=code)
