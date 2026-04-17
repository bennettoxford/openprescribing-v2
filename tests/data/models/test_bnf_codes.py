from openprescribing.data.models import BNFCode


def test_parts():
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


def test_is_generic():
    assert bnf_code("1001030U0AA").is_generic()
    assert not bnf_code("1001030U0BD").is_generic()
    assert bnf_code("1001030U0AAABAB").is_generic()
    assert not bnf_code("1001030U0BDAAAB").is_generic()


def test_is_ancestor_of():
    assert bnf_code("1001").is_ancestor_of(bnf_code("100103"))
    assert bnf_code("1001030U0").is_ancestor_of(bnf_code("1001030U0AA"))
    assert bnf_code("1001030U0AA").is_ancestor_of(bnf_code("1001030U0AAABAB"))
    assert not bnf_code("1001030U0AA").is_ancestor_of(bnf_code("1001030U0BDAAAB"))
    assert not bnf_code("1001030U0AA").is_ancestor_of(bnf_code("1001030U0AA"))


def test_is_generic_equivalent_of():
    assert bnf_code("1001030U0AAABAB").is_generic_equivalent_of(
        bnf_code("1001030U0BDAAAB")
    )
    assert not bnf_code("1001030U0AAABAB").is_generic_equivalent_of(
        bnf_code("1001030U0BDABAC")
    )


def test_strength_and_formulation_code():
    assert bnf_code("1001030U0AAABAB").strength_and_formulation_code == "1001030U0_AB"


def test_strength_and_formulation_name():
    assert (
        bnf_code(
            "1001030U0AAABAB",
            name="Methotrexate 2.5mg tablets",
        ).strength_and_formulation_name
        == "Methotrexate 2.5mg tablets"
    )


def test_strength_and_formulation_name_generic():
    assert (
        bnf_code(
            "0101021B0AAAGAG",
            name="Generic Gaviscon 500mg chewable tablets sugar free",
        ).strength_and_formulation_name
        == "Gaviscon 500mg chewable tablets sugar free"
    )


def bnf_code(code, name=""):
    level = {
        2: BNFCode.Level.CHAPTER,
        4: BNFCode.Level.SECTION,
        6: BNFCode.Level.PARAGRAPH,
        8: BNFCode.Level.SUBPARAGRAPH,
        9: BNFCode.Level.CHEMICAL_SUBSTANCE,
        11: BNFCode.Level.PRODUCT,
        15: BNFCode.Level.PRESENTATION,
    }[len(code)]
    return BNFCode(code=code, level=level, name=name)
