from functools import reduce

from django.db.models import Q

from ..models import BNFCode


def search(query):
    """Return BNF codes (as strings) of presentations matching query.

    A query is a list containing BNF codes at any level of the BNF hierarchy (again, as
    strings), which are optionally excluded with a leading "-".
    """

    includes = [Q(code__startswith=term) for term in query if term[0] != "-"]
    excludes = [Q(code__startswith=term[1:]) for term in query if term[0] == "-"]

    results = (
        BNFCode.objects.filter(level=BNFCode.Level.PRESENTATION)
        .filter(reduce(Q.__or__, includes))
        .order_by("code")
        .values_list("code", flat=True)
    )

    if excludes:
        results = results.exclude(reduce(Q.__or__, excludes))

    return list(results)
