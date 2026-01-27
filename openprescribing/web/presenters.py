from openprescribing.data.models import BNFCode


def make_bnf_tree(codes):
    lines = []
    level = 0

    for code in codes:
        assert code.level <= BNFCode.Level.CHEMICAL_SUBSTANCE
        if level < code.level:
            lines.append((level * 2, "<ul>"))
            level += 1
        else:
            lines.append((level * 2 - 1, "</li>"))
            while level > code.level:
                level -= 1
                lines.append((level * 2, "</ul>"))
                lines.append((level * 2 - 1, "</li>"))
        assert level == code.level
        lines.append(
            (level * 2 - 1, f'<li data-code="{code.code}" data-name="{code.name}">')
        )
        lines.append((level * 2, f"<span><code>{code.code}</code> {code.name}</span>"))

    while level > 0:
        lines.append((level * 2 - 1, "</li>"))
        level -= 1
        lines.append((level * 2, "</ul>"))

    return "\n".join(f"{'    ' * indent}{text}" for (indent, text) in lines)


def make_bnf_table(products, presentations):
    """Return headers and rows for a table containing all products and presentations
    belonging to a chemical substance.

    There is one header per product and one row per generic presentation.  (Or, for the
    chemical substances without generic presentations, one single row.)

    Each cell may contain any number of presentations.

    Products and presentations are represented as dictionaries with the keys "code" and
    "name".
    """
    headers = [to_dict(product) for product in products]

    generic_equivalents = [p for p in presentations if p.is_generic()]

    if generic_equivalents:
        rows = [[[] for _ in products] for _ in generic_equivalents]
        for p in presentations:
            row_ix = get_index(
                generic_equivalents,
                lambda ge: ge.is_generic_equivalent_of(p),
            )
            col_ix = get_index(
                products,
                lambda product: product.is_ancestor_of(p),
            )
            rows[row_ix][col_ix].append(to_dict(p))
    else:
        rows = [[[] for _ in products]]
        for p in presentations:
            col_ix = get_index(
                products,
                lambda product: product.is_ancestor_of(p),
            )
            rows[0][col_ix].append(to_dict(p))

    return headers, rows


def to_dict(bnf_code):
    return {"code": bnf_code.code, "name": bnf_code.name}


def get_index(lst, predicate):
    """Return the index of the single element of a list that matches a predicate."""
    matching_indexes = [ix for ix, e in enumerate(lst) if predicate(e)]
    assert len(matching_indexes) == 1
    return matching_indexes[0]
