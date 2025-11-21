from django.urls import path

from . import api, views


urlpatterns = [
    path("", views.index),
    path(
        "api/prescribing-deciles/",
        api.prescribing_deciles,
        name="api_prescribing_deciles",
    ),
]
