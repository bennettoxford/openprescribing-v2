from functools import reduce

from django.db.models import Q

from ..models import BNFCode


def search(query):
    """Return BNF codes (as strings) of presentations matching query.

    A query is a list of terms, where a term is either:

      * a BNF code (as a string) at any level of the hierarchy, which matches all
        presentations below that code;
      * a chemical's BNF code, followed by an underscore, followed by the two-character
        identifier for a strength and formulation (such as 040702040_AM for Tramadol HCl
        300mg tablets), which matches all presentations belonging to the chemical with
        the given strength and formulation.
    """

    fragments = [build_fragment(term) for term in query]
    includes = [f.build_q() for f in fragments if not f.negated]
    excludes = [f.build_q() for f in fragments if f.negated]

    results = (
        BNFCode.objects.filter(level=BNFCode.Level.PRESENTATION)
        .filter(reduce(Q.__or__, includes, Q()))
        .exclude(reduce(Q.__or__, excludes, Q()))
        .order_by("code")
        .values_list("code", flat=True)
    )

    return list(results)


def describe_search(query):
    """Return dictionary describing the query.

    See docstring of search() for description of query.
    """

    fragments = [build_fragment(term) for term in sorted(query)]
    return {
        "includes": [f.describe() for f in fragments if not f.negated],
        "excludes": [f.describe() for f in fragments if f.negated],
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

    def describe(self):
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

    def describe(self):
        generic_code_obj = BNFCode.objects.get(
            code=f"{self.prefix}AA{self.suffix}{self.suffix}"
        )
        description = f"{generic_code_obj.name} (branded and generic)"
        return {"code": self.term, "description": description}
