from django.urls import path

from . import api, views


urlpatterns = [
    path("", views.index),
    path("api/prescribing/", api.prescribing, name="api_prescribing"),
]
