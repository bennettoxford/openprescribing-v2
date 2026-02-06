from openprescribing.data.models import BNFCode, Org


def make_bnf_tree(codes):
    """Return list of nodes of representing a tree of BNF objects from chapters down to
    chemical substances.

    Each node is a dictionary representing a BNF object and its children.

    See tests.web.test_presenters.test_make_bnf_tree for an example of the output.
    """

    assert all(code.level <= BNFCode.Level.CHEMICAL_SUBSTANCE for code in codes)

    root = []
    stack = [(0, root)]  # tuples of (level, list of child nodes)

    for code in sorted(codes, key=lambda code: code.code):
        node = {"code": code.code, "name": code.name, "children": []}
        while stack and stack[-1][0] >= code.level:
            stack.pop()
        stack[-1][1].append(node)
        stack.append((code.level, node["children"]))

    return root


def make_bnf_table(products, presentations):
    """Return headers and rows for a table containing all products and presentations
    belonging to a chemical substance.

    There is one header per product and one row per generic presentation.  (Or, for the
    chemical substances without generic presentations, one single row.)

    Each row is represented as a dictionary with the keys "code" and "cells", where the
    code is the strength and formulation code of the generic presentation.  (Or None,
    for the chemical substances without generic presentations.)

    Each cell may contain any number of presentations.

    Products and presentations are represented as dictionaries with the keys "code" and
    "name".
    """
    headers = [to_dict(product) for product in products]

    generic_equivalents = [p for p in presentations if p.is_generic()]

    if generic_equivalents:
        rows = [
            {"code": ge.strength_and_formulation_code, "cells": [[] for _ in products]}
            for ge in generic_equivalents
        ]
        for p in presentations:
            row_ix = get_index(
                generic_equivalents,
                lambda ge: ge.is_generic_equivalent_of(p),
            )
            col_ix = get_index(
                products,
                lambda product: product.is_ancestor_of(p),
            )
            rows[row_ix]["cells"][col_ix].append(to_dict(p))
    else:
        rows = [{"code": None, "cells": [[] for _ in products]}]
        for p in presentations:
            col_ix = get_index(
                products,
                lambda product: product.is_ancestor_of(p),
            )
            rows[0]["cells"][col_ix].append(to_dict(p))

    return headers, rows


def to_dict(bnf_code):
    return {"code": bnf_code.code, "name": bnf_code.name}


def get_index(lst, predicate):
    """Return the index of the single element of a list that matches a predicate."""
    matching_indexes = [ix for ix, e in enumerate(lst) if predicate(e)]
    assert len(matching_indexes) == 1
    return matching_indexes[0]


def make_orgs():
    org_type_levels = [c[0] for c in Org.OrgType.choices]
    orgs = sorted(
        Org.objects.order_by("name").values("id", "name", "org_type"),
        key=lambda o: org_type_levels.index(o["org_type"]),
    )
    return orgs
