from collections import namedtuple

from openprescribing.data.models import BNFCode, Org


def make_bnf_tree(codes):
    """Return list of nodes representing the BNF browser tree.

    Chapters 01 to 19 are shown from chapter down to chemical substance. Chapters 20+
    use a flatter structure of chapter -> section -> product.

    Each node is a dictionary representing a BNF object and its children. Nodes also
    include a ``node_type`` used by the browser frontend.

    See tests.web.test_presenters.test_make_bnf_tree for an example of the output.
    """

    root = []
    nodes_by_code = {}

    for code in sorted(codes, key=lambda code: code.code):
        node_type = get_bnf_browser_node_type(code)
        if node_type is None:
            continue

        node = {
            "code": code.code,
            "name": code.name,
            "node_type": node_type,
            "children": [],
        }
        parent_code = get_bnf_browser_parent_code(code)
        if parent_code is None:
            root.append(node)
        else:
            nodes_by_code[parent_code]["children"].append(node)
        nodes_by_code[code.code] = node

    return root


def get_bnf_browser_node_type(code):
    if is_devices_chapter(code.code):
        node_types = {
            BNFCode.Level.CHAPTER: "chapter",
            BNFCode.Level.SECTION: "section",
            BNFCode.Level.PRODUCT: "product",
        }
    else:
        node_types = {
            BNFCode.Level.CHAPTER: "chapter",
            BNFCode.Level.SECTION: "section",
            BNFCode.Level.PARAGRAPH: "paragraph",
            BNFCode.Level.SUBPARAGRAPH: "subparagraph",
            BNFCode.Level.CHEMICAL_SUBSTANCE: "chemical-substance",
        }
    return node_types.get(code.level)


def get_bnf_browser_parent_code(code):
    if code.level == BNFCode.Level.CHAPTER:
        return None

    if is_devices_chapter(code.code):
        parent_lengths = {
            BNFCode.Level.SECTION: 2,
            BNFCode.Level.PRODUCT: 4,
        }
    else:
        parent_lengths = {
            BNFCode.Level.SECTION: 2,
            BNFCode.Level.PARAGRAPH: 4,
            BNFCode.Level.SUBPARAGRAPH: 6,
            BNFCode.Level.CHEMICAL_SUBSTANCE: 7,
        }

    parent_length = parent_lengths.get(code.level)
    if parent_length is None:
        return None
    return code.code[:parent_length]


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


def make_ntr_dtr_intersection_table(ntr_query, dtr_query):
    # This is going to double-up on some work done by the `/api` call that will
    # typically happen on the same page, but I don't think there's much we can do about
    # that with the current architecture.
    # If this function is problematically slow, we could look at optimising
    # it by pushing this logic out of `web` & into `data` & doing more in the
    # database server (rather than in Python).
    ntr_codes_full = ntr_query.get_matching_presentation_codes()
    all_codes = set(ntr_codes_full)

    has_denominators = bool(dtr_query)
    if has_denominators:
        dtr_codes_full = dtr_query.get_matching_presentation_codes()
        all_codes = all_codes | set(dtr_codes_full)

    # I think it's very appropriate to sort by code here, as the BNF code
    # hierarchy implicitly means that presentations are sorted together usefully.
    # This is in contrast to the codes seen in OpenPrescribing Hospitals.
    all_codes = sorted(all_codes)
    relevant_bnf_code_names = dict(
        BNFCode.objects.filter(code__in=all_codes)
        .order_by("code")
        .values_list("code", "name")
    )

    Presentation = namedtuple("Presentation", "code, name, ntr, dtr")
    data = [
        Presentation(
            code,
            relevant_bnf_code_names[code],
            code in ntr_codes_full,
            code in dtr_codes_full if has_denominators else None,
        )
        for code in all_codes
    ]
    return {"has_denominators": has_denominators, "data": data}


def make_code_to_name(codes):
    """Return mapping from BNF code to BNF name.

    For now, users can only select BNF objects down to the chemical substance level, or
    all presentations that are clinically equivalent.  As such, we ignore all other
    codes.
    """

    code_to_name = {}
    for c in codes:
        if c.level <= BNFCode.Level.CHEMICAL_SUBSTANCE:
            code_to_name[c.code] = c.name
        if c.level == BNFCode.Level.PRESENTATION and c.is_generic():
            code_to_name[c.strength_and_formulation_code] = (
                c.strength_and_formulation_name
            )
    return code_to_name


def is_devices_chapter(code):
    return int(code[:2]) >= 20
