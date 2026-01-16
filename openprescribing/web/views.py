from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from openprescribing.data.models import BNFCode, Org


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
        api_url = f"{reverse('api_prescribing_deciles')}?codes={code}"
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
    codes = request.GET.get("codes", "")
    org_id = request.GET.get("org_id")

    bnf_codes_inclusion = []
    bnf_codes_exclusion = []
    for code in codes.split():
        if code[0] == "-":
            bnf_codes_exclusion.append(get_object_or_404(BNFCode, code=code[1:]))
        else:
            bnf_codes_inclusion.append(get_object_or_404(BNFCode, code=code))

    org = None
    api_url = None

    if org_id:
        org = get_object_or_404(Org, id=org_id)

    if codes:
        api_url = (
            f"{reverse('api_prescribing_deciles')}?codes={','.join(codes.split())}"
        )
        if org_id:
            api_url += f"&org_id={org_id}"

    ctx = {
        "codes": codes,
        "bnf_codes_inclusion": bnf_codes_inclusion,
        "bnf_codes_exclusion": bnf_codes_exclusion,
        "org": org,
        "prescribing_api_url": api_url,
    }

    return render(request, "bnf_codes.html", ctx)
