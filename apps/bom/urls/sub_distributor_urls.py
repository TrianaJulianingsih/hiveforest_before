from django.urls import path
from apps.bom.views.sub_distributor_views import (
    sub_distributor_list,
    sub_distributor_dashboard,
    sub_distributor_add,
    sub_distributor_save,
    sub_distributor_update_subdist,
)

urlpatterns = [
    path("", sub_distributor_list, name="sub_distributor_list"),
    path("dashboard/", sub_distributor_dashboard, name="sub_distributor_dashboard"),
    path("add/", sub_distributor_add, name="sub_distributor_add"),
    path("save/", sub_distributor_save, name="sub_distributor_save"),
    path("<int:id>/update-subdist/", sub_distributor_update_subdist, name="sub_distributor_update_subdist"),
]
