from django.urls import path

from . import api, views


urlpatterns = [
    path("", views.analysis, name="analysis"),
    path("analysis/build/", views.build_analysis, name="build-analysis"),
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
    path(
        "api/metadata/medications/",
        api.metadata_medications,
        name="api_metadata_medications",
    ),
    path("feedback/vote/", views.feedback_vote, name="feedback_vote"),
    path("feedback/comment/", views.feedback_comment, name="feedback_comment"),
    path("bnf/", views.bnf_browser_tree),
    path("bnf/<slug:code>/", views.bnf_browser_table),
    path("measures/", views.all_measures),
    path("measures/<slug:measure_name>/", views.measure),
]
