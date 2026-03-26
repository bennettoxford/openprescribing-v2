from django.urls import path

from . import api, views


urlpatterns = [
    path("", views.analysis),
    path(
        "api/prescribing-deciles/",
        api.prescribing_deciles,
        name="api_prescribing_deciles",
    ),
    path(
        "api/prescribing-all-orgs/",
        api.prescribing_all_orgs,
        name="api_prescribing_all_orgs",
    ),
    path("bnf/", views.bnf_browser_tree),
    path("bnf/<slug:code>/", views.bnf_browser_table),
    path("feedback/thumb/<int:thumb>", views.feedback_thumb),
    path("feedback/text/<int:thumb>", views.feedback_text, name="feedback_text"),
]
