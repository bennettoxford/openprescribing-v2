import pytest

from openprescribing.data.models import BNFCode


@pytest.mark.django_db(databases=["data"])
def test_parts(bnf_codes):
    parts_of_chapter = bnf_code("10").parts
    assert parts_of_chapter.chapter == "10"
    assert parts_of_chapter.section is None
    assert parts_of_chapter.paragraph is None
    assert parts_of_chapter.subparagraph is None
    assert parts_of_chapter.chemical_substance is None
    assert parts_of_chapter.product is None
    assert parts_of_chapter.strength_and_formulation is None
    assert parts_of_chapter.generic_equivalent is None

    parts_of_presentation = bnf_code("1001030U0BDABAC").parts
    assert parts_of_presentation.chapter == "10"
    assert parts_of_presentation.section == "01"
    assert parts_of_presentation.paragraph == "03"
    assert parts_of_presentation.subparagraph == "0"
    assert parts_of_presentation.chemical_substance == "U0"
    assert parts_of_presentation.product == "BD"
    assert parts_of_presentation.strength_and_formulation == "AB"
    assert parts_of_presentation.generic_equivalent == "AC"


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


@pytest.mark.django_db(databases=["data"])
def test_strength_and_formulation_code(bnf_codes):
    assert bnf_code("1001030U0AAABAB").strength_and_formulation_code == "1001030U0_AB"


@pytest.mark.django_db(databases=["data"])
def test_strength_and_formulation_name(bnf_codes):
    assert (
        bnf_code("1001030U0AAABAB").strength_and_formulation_name
        == "Methotrexate 2.5mg tablets (branded and generic)"
    )


def bnf_code(code):
    return BNFCode.objects.get(code=code)
