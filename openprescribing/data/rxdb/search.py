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

    includes = [_build_q(term) for term in query if term[0] != "-"]
    excludes = [_build_q(term[1:]) for term in query if term[0] == "-"]

    results = (
        BNFCode.objects.filter(level=BNFCode.Level.PRESENTATION)
        .filter(reduce(Q.__or__, includes, Q()))
        .exclude(reduce(Q.__or__, excludes, Q()))
        .order_by("code")
        .values_list("code", flat=True)
    )

    return list(results)


def _build_q(term):
    if "_" in term:
        assert term.count("_") == 1
        prefix, suffix = term.split("_")
        assert len(prefix) == 9  # chemical code
        assert len(suffix) == 2  # strength and formulation
        return Q(code__startswith=prefix, code__endswith=suffix)
    else:
        return Q(code__startswith=term)
