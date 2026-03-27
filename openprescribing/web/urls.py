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
    path("feedback/vote/", views.feedback_vote, name="feedback_vote"),
    path("feedback/detail/", views.feedback_detail, name="feedback_detail"),
    path("bnf/", views.bnf_browser_tree),
    path("bnf/<slug:code>/", views.bnf_browser_table),
]
