from django.urls import path
from apps.sales.views.dashboard_views import (
    sales_dashboard,
    ecatalog_dashboard,
    iqvia_itma_dashboard,
)

urlpatterns = [
    path("bi/dashboard/sales", sales_dashboard, name="sales_dashboard"),
    path("bi/dashboard/ecatalog", ecatalog_dashboard, name="ecatalog_dashboard"),
    path("bi/dashboard/iqvia_itma", iqvia_itma_dashboard, name="iqvia_itma_dashboard"),
]
