from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from openprescribing.data.models import BNFCode, Org


def index(request):
    code = request.GET.get("code")
    practice_id = request.GET.get("practice_id")

    bnf_code = None
    practice = None
    api_url = None

    if practice_id:
        practice = get_object_or_404(Org, id=practice_id, org_type=Org.OrgType.PRACTICE)

    if code:
        bnf_code = get_object_or_404(BNFCode, code=code)
        api_url = f"{reverse('api_prescribing')}?code={code}"
        if practice_id:
            api_url += f"&practice_id={practice_id}"

    ctx = {
        "bnf_code": bnf_code,
        "bnf_codes": list(BNFCode.objects.order_by("level", "name").values()),
        "bnf_levels": BNFCode.Level.choices,
        "practice": practice,
        "practices": list(
            Org.objects.filter(org_type=Org.OrgType.PRACTICE)
            .order_by("name")
            .values("id", "name")
        ),
        "prescribing_api_url": api_url,
    }

    return render(request, "index.html", ctx)
