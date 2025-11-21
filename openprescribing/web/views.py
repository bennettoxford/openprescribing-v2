from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from openprescribing.data.models import BNFCode, Org


def index(request):
    code = request.GET.get("code")
    org_id = request.GET.get("org_id")

    bnf_code = None
    org = None
    api_url = None

    if org_id:
        org = get_object_or_404(Org, id=org_id, org_type=Org.OrgType.PRACTICE)

    if code:
        bnf_code = get_object_or_404(BNFCode, code=code)
        api_url = f"{reverse('api_prescribing')}?code={code}"
        if org_id:
            api_url += f"&org_id={org_id}"

    ctx = {
        "bnf_code": bnf_code,
        "bnf_codes": list(BNFCode.objects.order_by("level", "name").values()),
        "bnf_levels": BNFCode.Level.choices,
        "org": org,
        "orgs": list(
            Org.objects.filter(org_type=Org.OrgType.PRACTICE)
            .order_by("name")
            .values("id", "name")
        ),
        "prescribing_api_url": api_url,
    }

    return render(request, "index.html", ctx)
