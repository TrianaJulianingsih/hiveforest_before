from django.urls import path

from apps.crm.views.dashboard_views import (
    analytics_dashboard,
    export_csv,
    export_excel,
    hcp_filter_options,
    hcp_list,
    hcp_profile,
    hcp_profile_dashboard,
    hcp_suggest,
    hospital_export_csv,
    hospital_export_excel,
    hospital_filter_options,
    hospital_list,
    hospital_profile,
    hospital_profile_dashboard,
    hospital_suggest,
)

urlpatterns = [
    path("hcp/", hcp_list, name="hcp_list"),
    path("hcp/profile/", hcp_profile_dashboard, name="hcp_profile_dashboard"),
    path("hcp/<int:pk>/", hcp_profile, name="hcp_profile"),
    path("hospital/", hospital_list, name="hospital_list"),
    path("hospital/profile/", hospital_profile_dashboard, name="hospital_profile_dashboard"),
    path("hospital/suggest/", hospital_suggest, name="hospital_suggest"),
    path("hospital/filter-options/", hospital_filter_options, name="hospital_filter_options"),
    path("hospital/export/csv/", hospital_export_csv, name="hospital_export_csv"),
    path("hospital/export/excel/", hospital_export_excel, name="hospital_export_excel"),
    path("hospital/<int:pk>/", hospital_profile, name="hospital_profile"),
    path("analytics/", analytics_dashboard, name="analytics_dashboard"),
    path("export/csv/", export_csv, name="export_csv"),
    path("export/excel/", export_excel, name="export_excel"),
    path("suggest/", hcp_suggest, name="hcp_suggest"),
    path("filter-options/", hcp_filter_options, name="hcp_filter_options"),
]
