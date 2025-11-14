from django.shortcuts import render
from django.urls import reverse

from openprescribing.data.models import BNFCode


def index(request):
    code = request.GET.get("code")
    bnf_code = BNFCode.objects.get(code=code)
    api_url = f"{reverse('api_prescribing')}?code={code}"
    ctx = {"bnf_code": bnf_code, "prescribing_api_url": api_url}
    return render(request, "index.html", ctx)
