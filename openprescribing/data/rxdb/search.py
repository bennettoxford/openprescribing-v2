from enum import StrEnum
from functools import reduce

from django.db.models import Q

from ..models import BNFCode


class ProductType(StrEnum):
    ALL = "all"
    GENERIC = "generic"
    BRANDED = "branded"


def search(terms, product_type):
    """Return the BNF presentation codes (as strings) that match the given query.

    A query is a list of terms (as strings) and a product type.

    A term is either:

    * any BNF code. All BNF presentation codes that are descendants of this
      BNF code are matched; or

    * a BNF chemical substance code (nine-characters), an underscore, and
      a strength and formulation component (two-characters). The underscore is a
      wild card that replaces the product component (two-characters). All
      BNF presentation codes that are descendants of this BNF chemical substance code,
      and have this strength and formulation component, are matched. For example,
      "040702040_AM" matches "040702040AAAMAM", which is the BNF presentation code for
      "Tramadol 300mg modified-release tablets".

    A product type filters the matched BNF presentation codes to generic, branded,
    or all products.
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

        # A BNF strength and formulation code has 13 characters. However, we expect
        # the product component (two characters) to be replaced by an underscore.
        assert len(term) == 12
        assert term[9] == "_"

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
