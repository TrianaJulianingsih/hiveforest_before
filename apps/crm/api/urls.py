from django.urls import path

from .views import (
    DoctorDashboardView,
    DoctorDetailView,
    DoctorExportView,
    DoctorListView,
    HospitalDetailView,
    HospitalExportView,
    HospitalListView,
)

urlpatterns = [
    # export/, dashboard/ must come before <int:pk>/ for readability, though the int
    # converter alone would already reject non-numeric segments like "export".
    path("hospitals/export/", HospitalExportView.as_view(), name="crm-api-hospital-export"),
    path("hospitals/", HospitalListView.as_view(), name="crm-api-hospital-list"),
    path("hospitals/<int:pk>/", HospitalDetailView.as_view(), name="crm-api-hospital-detail"),
    path("doctors/export/", DoctorExportView.as_view(), name="crm-api-doctor-export"),
    path("doctors/dashboard/", DoctorDashboardView.as_view(), name="crm-api-doctor-dashboard"),
    path("doctors/", DoctorListView.as_view(), name="crm-api-doctor-list"),
    path("doctors/<int:pk>/", DoctorDetailView.as_view(), name="crm-api-doctor-detail"),
]
