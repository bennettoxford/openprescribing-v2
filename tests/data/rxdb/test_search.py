import pytest

from openprescribing.data.rxdb import search


@pytest.mark.django_db(databases=["data"])
def test_search(bnf_codes):
    assert search(["1001030U0AA", "1001030U0BD", "-1001030U0AAABAB"]) == [
        "1001030U0AAACAC",
        "1001030U0BDAAAB",
        "1001030U0BDABAC",
    ]


@pytest.mark.django_db(databases=["data"])
def test_search_no_excludes(bnf_codes):
    assert search(["1001030U0AA"]) == ["1001030U0AAABAB", "1001030U0AAACAC"]


@pytest.mark.django_db(databases=["data"])
def test_search_for_strength_and_formulation(bnf_codes):
    assert search(["1001030U0_AC"]) == ["1001030U0AAACAC", "1001030U0BDABAC"]
