from django.urls import path

from . import views

app_name = "audits"

urlpatterns = [
    path("", views.index, name="index"),
    path("analyze/", views.analyze, name="analyze"),
    path("report/<int:audit_id>/", views.report, name="report"),
]
