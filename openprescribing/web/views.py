import platform

from django.http import HttpResponse


def index(request):
    hostname = platform.node()
    return HttpResponse(f"Welcome to OPv2 on {hostname}")
