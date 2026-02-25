import altair as alt
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from openprescribing.data.models import BNFCode, Org
from openprescribing.data.rxdb.search import describe_search

from .presenters import (
    make_bnf_table,
    make_bnf_tree,
    make_ntr_dtr_intersection_table,
    make_orgs,
)


def query(request):
    ntr_codes_raw = request.GET.get("ntr_codes")
    ntr_product_type = request.GET.get("ntr_product_type", "all")
    dtr_codes_raw = request.GET.get("dtr_codes")
    dtr_product_type = request.GET.get("dtr_product_type", "all")
    org_id = request.GET.get("org_id")

    deciles_api_url = None
    all_orgs_api_url = None
    ntr_description = None
    dtr_description = None
    org = None
    ntr_dtr_intersection_table = None

    if org_id:
        org = get_object_or_404(Org, id=org_id)

    if ntr_codes_raw:
        ntr_codes = ntr_codes_raw.split()
        url_parameters = (
            f"?ntr_codes={','.join(ntr_codes)}&ntr_product_type={ntr_product_type}"
        )
        ntr_description = describe_search(ntr_codes, ntr_product_type)

        if dtr_codes_raw:
            dtr_codes = dtr_codes_raw.split()
            url_parameters += (
                f"&dtr_codes={','.join(dtr_codes)}&dtr_product_type={dtr_product_type}"
            )
            dtr_description = describe_search(dtr_codes, dtr_product_type)
            ntr_dtr_intersection_table = make_ntr_dtr_intersection_table(
                ntr_codes, ntr_product_type, dtr_codes, dtr_product_type
            )
        else:
            dtr_description = {"text": "1000 patients"}
            ntr_dtr_intersection_table = make_ntr_dtr_intersection_table(
                ntr_codes, ntr_product_type
            )

        if org_id:
            url_parameters += f"&org_id={org_id}"

        deciles_api_url = f"{reverse('api_prescribing_deciles')}{url_parameters}"
        all_orgs_api_url = f"{reverse('api_prescribing_all_orgs')}{url_parameters}"

    codes = (
        BNFCode.objects.filter(level__lte=BNFCode.Level.CHEMICAL_SUBSTANCE)
        .exclude(code__startswith="2")
        .order_by("code")
    )
    tree = make_bnf_tree(codes)

    orgs = make_orgs()

    x = alt.X("month:T", title="Month", axis=alt.Axis(format="%Y %b"))
    y = alt.Y("value:Q", title="%" if dtr_codes_raw else "Items per 1000 patients")
    stroke_dash = (
        alt.when(alt.datum.centile == 50)
        .then(alt.value((6, 2)))
        .otherwise(alt.value((2, 6)))
    )
    deciles_chart = (
        alt.Chart(alt.NamedData("deciles"))
        .mark_line(color="blue")
        .encode(x=x, y=y, detail="centile:O", strokeDash=stroke_dash)
        .properties(width=660, height=360)
    )
    org_chart = alt.Chart(alt.NamedData("org")).mark_line(color="red").encode(x=x, y=y)
    deciles_chart += org_chart
    all_orgs_line_chart = (
        alt.Chart(alt.NamedData("all_orgs_line_chart"))
        .mark_line(color="grey", opacity=0.2)
        .encode(x=x, y=y, detail="org:O")
        .properties(width=660, height=360)
    )
    deciles_chart += all_orgs_line_chart

    ctx = {
        "ntr_codes": ntr_codes_raw,
        "ntr_product_type": ntr_product_type,
        "ntr_description": ntr_description,
        "dtr_codes": dtr_codes_raw,
        "dtr_product_type": dtr_product_type,
        "dtr_description": dtr_description,
        "ntr_dtr_intersection_table": ntr_dtr_intersection_table,
        "org": org,
        "orgs": orgs,
        "org_types": Org.OrgType.choices,
        "prescribing_deciles_url": deciles_api_url,
        "prescribing_all_orgs_url": all_orgs_api_url,
        "tree": tree,
        "deciles_chart": deciles_chart.to_dict(),
    }

    return render(request, "query.html", ctx)


def bnf_browser_tree(request):
    """This view renders an interactive tree for chapters 01 to 19 of the BNF hierarchy.
    Nodes include BNF codes down to the chemical substance level.  For products and
    presentations, see bnf_browser_table.

    Chapters 20 to 23 (devices rather than medicines) have a slightly different code
    structure, and so will need to be handled slightly differently.
    """

    codes = (
        BNFCode.objects.filter(level__lte=BNFCode.Level.CHEMICAL_SUBSTANCE)
        .exclude(code__startswith="2")
        .order_by("code")
    )
    ctx = {"tree": make_bnf_tree(codes)}
    return render(request, "bnf_browser_tree.html", ctx)


def bnf_browser_table(request, code):
    """This view renders a table showing all of the products and presentations belonging
    to a chemical substance.

    See docstring of make_bnf_table for a description of the structure of the table.
    """

    # Although we don't use the object found here, we want to return a 404 if the code
    # doesn't correspond to a chemical substance.
    get_object_or_404(BNFCode, code=code, level=BNFCode.Level.CHEMICAL_SUBSTANCE)
    products = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRODUCT
    ).order_by("code")
    presentations = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRESENTATION
    ).order_by("code")

    headers, rows = make_bnf_table(products, presentations)

    ctx = {"headers": headers, "rows": rows}
    return render(request, "bnf_browser_table.html", ctx)
