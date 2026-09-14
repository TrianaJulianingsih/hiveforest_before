from django.urls import path
from apps.bom.views.freight_cost_views import (
    freight_cost_list,
    freight_cost_dashboard,
    freight_cost_data,
    freight_cost_export,
    freight_cost_export_progress,
)

urlpatterns = [
    path("", freight_cost_list, name="freight_cost_list"),
    path("dashboard/", freight_cost_dashboard, name="freight_cost_dashboard"),
    path("data/", freight_cost_data, name="freight_cost_data"),
    path("export/", freight_cost_export, name="freight_cost_export"),
    path("export-progress/", freight_cost_export_progress, name="freight_cost_export_progress"),
]
