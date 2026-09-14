from django.urls import path, include
from apps.bom.views.dashboard_bom_views import dash_distribution, dash_stock
from apps.bom.views.sub_distributor_views import sub_distributor_dashboard
from apps.bom.views.branchstock_report_views import (
    branchstock_summary,
    branchstock_summary_user,
    branchstock_summary_dashboard,
)
from apps.bom.views.freight_cost_views import freight_cost_dashboard

app_name = "bom"

urlpatterns = [
    path("bi/dashboard/distribution/", dash_distribution, name="dash_distribution"),
    path("bi/dashboard/stock/", dash_stock, name="dash_stock"),
    
    path(
        "customer-maintenance/sub-distributor/",
        include("apps.bom.urls.sub_distributor_urls"),
    ),
    
    path("dashboard/sub-distributor/", sub_distributor_dashboard, name="dash_sub_distributor"),
    
    path(
        "freight-cost/freightcost/",
        include("apps.bom.urls.freight_cost_urls"),
    ),
    path("freight-cost/dashboard/", freight_cost_dashboard, name="dash_freight_cost"),
    
    path(
        "warehouse-palettes/",
        include(
            ("apps.bom.urls.warehouse_palettes_urls", "bom"), namespace="warehouse_palettes"
        ),
    ),
    
    path("branchstock_summary/", branchstock_summary, name="branchstock_summary"),
    path(
        "branchstocksummary/dashboard/",
        branchstock_summary_dashboard,
        name="branchstock_summary_dashboard",
    ),
    path(
        "branchstocksummary/user/",
        branchstock_summary_user,
        name="branchstock_summary_user",
    ),
]
