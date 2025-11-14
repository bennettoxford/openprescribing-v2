from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from openprescribing.data.models import BNFCode


def index(request):
    code = request.GET.get("code")

    if code:
        bnf_code = get_object_or_404(BNFCode, code=code)
        api_url = f"{reverse('api_prescribing')}?code={bnf_code.code}"
    else:
        bnf_code = None
        api_url = None

    ctx = {
        "bnf_codes": list(BNFCode.objects.order_by("level", "name").values()),
        "bnf_levels": BNFCode.Level.choices,
        "bnf_code": bnf_code,
        "prescribing_api_url": api_url,
    }

    return render(request, "index.html", ctx)
