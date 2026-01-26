from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from openprescribing.data.models import BNFCode, Org
from openprescribing.data.rxdb.search import describe_search


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
