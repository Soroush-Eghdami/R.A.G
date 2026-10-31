from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("models/", views.models, name="models"),
    path("settings/", views.app_settings, name="app-settings"),
]
