from django.urls import path

from . import api, views


urlpatterns = [
    path("bnf_codes/", views.query),
    path(
        "api/prescribing-deciles/",
        api.prescribing_deciles,
        name="api_prescribing_deciles",
    ),
    path("bnf/", views.bnf_browser_tree),
    path("bnf/<slug:code>/", views.bnf_browser_table),
]
