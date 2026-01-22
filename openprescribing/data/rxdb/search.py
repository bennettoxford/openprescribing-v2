from enum import StrEnum
from functools import reduce

from django.db.models import Q

from ..models import BNFCode


class ProductType(StrEnum):
    ALL = "all"
    GENERIC = "generic"
    BRANDED = "branded"


def search(terms, product_type):
    """Return BNF codes (as strings) of presentations matching query.

    A query is a list of terms and an indication of whether to search for only generic
    or branded presentations.

    A term is either:

      * a BNF code (as a string) at any level of the hierarchy, which matches all
        presentations below that code;
      * a chemical's BNF code, followed by an underscore, followed by the two-character
        identifier for a strength and formulation (such as 040702040_AM for Tramadol HCl
        300mg tablets), which matches all presentations belonging to the chemical with
        the given strength and formulation.
    """

    fragments = [build_fragment(term) for term in terms]
    includes = [f.build_q() for f in fragments if not f.negated]
    excludes = [f.build_q() for f in fragments if f.negated]

    codes = list(
        BNFCode.objects.filter(level=BNFCode.Level.PRESENTATION)
        .filter(reduce(Q.__or__, includes, Q()))
        .exclude(reduce(Q.__or__, excludes, Q()))
        .order_by("code")
        .values_list("code", flat=True)
    )

    if product_type == ProductType.ALL:
        return codes
    elif product_type == ProductType.GENERIC:
        return [c for c in codes if c[9:11] == "AA"]
    elif product_type == ProductType.BRANDED:
        return [c for c in codes if c[9:11] != "AA"]
    else:
        assert False, product_type


def describe_search(terms, product_type):
    """Return dictionary describing the query.

    See docstring of search() for description of query.
    """

    fragments = [build_fragment(term) for term in sorted(terms)]
    return {
        "product_type": product_type,
        "includes": [f.describe(product_type) for f in fragments if not f.negated],
        "excludes": [f.describe(product_type) for f in fragments if f.negated],
    }


def build_fragment(term):
    if term[0] == "-":
        negated = True
        term = term[1:]
    else:
        negated = False
    if "_" in term:
        return StrengthAndFormulationFragment(term, negated)
    else:
        return PrefixFragment(term, negated)


class PrefixFragment:
    def __init__(self, term, negated):
        self.term = term
        self.negated = negated

    def build_q(self):
        return Q(code__startswith=self.term)

    def describe(self, product_type):
        description = BNFCode.objects.get(code=self.term).name
        return {"code": self.term, "description": description}


class StrengthAndFormulationFragment:
    def __init__(self, term, negated):
        self.term = term
        self.negated = negated
        assert term.count("_") == 1
        self.prefix, self.suffix = term.split("_")
        assert len(self.prefix) == 9  # chemical code
        assert len(self.suffix) == 2  # strength and formulation

    def build_q(self):
        return Q(code__startswith=self.prefix, code__endswith=self.suffix)

    def describe(self, product_type):
        generic_code_obj = BNFCode.objects.get(
            code=f"{self.prefix}AA{self.suffix}{self.suffix}"
        )
        if product_type == ProductType.ALL:
            description = f"{generic_code_obj.name} (branded and generic)"
        else:
            description = generic_code_obj.name
        return {"code": self.term, "description": description}
