from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from openprescribing.data.models import BNFCode, Org
from openprescribing.data.rxdb.search import describe_search

from .presenters import make_bnf_table, make_bnf_tree


def index(request):
    return render(request, "index.html")


def bnf_code(request):
    code = request.GET.get("code")
    org_id = request.GET.get("org_id")

    bnf_code = None
    org = None
    api_url = None

    if org_id:
        org = get_object_or_404(Org, id=org_id)

    if code:
        bnf_code = get_object_or_404(BNFCode, code=code)
        api_url = f"{reverse('api_prescribing_deciles')}?ntr_codes={code}"
        if org_id:
            api_url += f"&org_id={org_id}"

    bnf_codes = list(BNFCode.objects.order_by("level", "name").values())
    org_type_levels = [c[0] for c in Org.OrgType.choices]
    orgs = sorted(
        Org.objects.order_by("name").values("id", "name", "org_type"),
        key=lambda o: org_type_levels.index(o["org_type"]),
    )

    ctx = {
        "bnf_code": bnf_code,
        "bnf_codes": bnf_codes,
        "bnf_levels": BNFCode.Level.choices,
        "org": org,
        "orgs": orgs,
        "org_types": Org.OrgType.choices,
        "prescribing_api_url": api_url,
    }

    return render(request, "bnf_code.html", ctx)


def bnf_codes(request):
    ntr_codes_raw = request.GET.get("ntr_codes")
    ntr_product_type = request.GET.get("ntr_product_type", "all")
    dtr_codes_raw = request.GET.get("dtr_codes")
    dtr_product_type = request.GET.get("dtr_product_type", "all")

    api_url = None
    ntr_description = None
    dtr_description = None

    if ntr_codes_raw:
        ntr_codes = ntr_codes_raw.split()
        api_url = f"{reverse('api_prescribing_deciles')}?ntr_codes={','.join(ntr_codes)}&ntr_product_type={ntr_product_type}"
        ntr_description = describe_search(ntr_codes, ntr_product_type)

        if dtr_codes_raw:
            dtr_codes = dtr_codes_raw.split()
            api_url += (
                f"&dtr_codes={','.join(dtr_codes)}&dtr_product_type={dtr_product_type}"
            )
            dtr_description = describe_search(dtr_codes, dtr_product_type)
        else:
            dtr_description = {"text": "1000 patients"}

    ctx = {
        "ntr_codes": ntr_codes_raw,
        "ntr_product_type": ntr_product_type,
        "ntr_description": ntr_description,
        "dtr_codes": dtr_codes_raw,
        "dtr_product_type": dtr_product_type,
        "dtr_description": dtr_description,
        "prescribing_api_url": api_url,
    }

    return render(request, "bnf_codes.html", ctx)


def bnf_browser_tree(request):
    """This view renders an interactive tree for chapters 01 to 19 of the BNF hierarchy.
    Nodes include BNF codes down to the chemical substance level.  For products and
    presentations, see bnf_browser_table.
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

    chemical = get_object_or_404(
        BNFCode, code=code, level=BNFCode.Level.CHEMICAL_SUBSTANCE
    )
    products = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRODUCT
    ).order_by("code")
    presentations = BNFCode.objects.filter(
        code__startswith=code, level=BNFCode.Level.PRESENTATION
    ).order_by("code")

    headers, rows = make_bnf_table(products, presentations)

    ctx = {"chemical": chemical, "headers": headers, "rows": rows}
    return render(request, "bnf_browser_table.html", ctx)
