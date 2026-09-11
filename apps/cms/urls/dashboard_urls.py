from django.urls import path
from apps.cms.views.dashboard_views import dashboard_views

app_name = "cms"

urlpatterns = [
    path("dashboard_views/", dashboard_views, name="dashboard_views"),
]
