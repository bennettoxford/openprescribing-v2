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
    generic_equivalents = [p for p in presentations if p.is_generic()]
    if generic_equivalents:
        num_rows = len(generic_equivalents)
        cells = [[[] for _ in products] for _ in generic_equivalents]
        for p in presentations:
            row_ix = get_index(
                generic_equivalents,
                lambda ge: ge.is_generic_equivalent_of(p),
            )
            col_ix = get_index(
                products,
                lambda product: product.is_ancestor_of(p),
            )
            cells[row_ix][col_ix].append(p)
    else:
        num_rows = 1
        cells = [[[] for _ in products]]
        for p in presentations:
            col_ix = get_index(
                products,
                lambda product: product.is_ancestor_of(p),
            )
            cells[0][col_ix].append(p)

    lines = [
        '<table class="table table-sm">',
        "  <tr>",
    ]

    for product in products:
        lines.append(f"    <th><code>{product.code}</code><br />{product.name}</th>")
    lines.append("  </tr>")
    for row_ix in range(num_rows):
        lines.append("  <tr>")
        for col_ix in range(len(products)):
            lines.append("    <td>")
            lines.append("      <ul>")
            for presentation in cells[row_ix][col_ix]:
                lines.append(
                    f"        <li><code>{presentation.code}</code><br />{presentation.name}</li>"
                )
            lines.append("      </ul>")
            lines.append("    </td>")
        lines.append("  </tr>")
    lines.append("</table>")

    return "\n".join(lines)


def get_index(lst, predicate):
    """Return the index of the single element of a list that matches a predicate."""
    matching_indexes = [ix for ix, e in enumerate(lst) if predicate(e)]
    assert len(matching_indexes) == 1
    return matching_indexes[0]
