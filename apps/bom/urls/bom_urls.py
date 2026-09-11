from django.urls import path, include
from apps.bom.views.dash_bomviews import dash_distribution, dash_stock
from apps.bom.views.sub_distributor import (
    sub_distributor_list,
    sub_distributor_add,
    sub_distributor_save,
    sub_distributor_update_subdist,
)
from apps.bom.views.freight_cost import (
    freight_cost_data,
    freight_cost_export,
    freight_cost_export_progress,
    freight_cost_list,
)
from apps.bom.views.branchstock_report import (
    branchstock_summary,
    branchstock_summary_user,
)

app_name = "bom"

urlpatterns = [
    path("bi/dashboard/distribution/", dash_distribution, name="dash_distribution"),
    path("bi/dashboard/stock/", dash_stock, name="dash_stock"),
    
    path(
        "customer-maintenance/sub-distributor/",
        sub_distributor_list,
        name="sub_distributor_list",
    ),
    path(
        "customer-maintenance/sub-distributor/add/",
        sub_distributor_add,
        name="sub_distributor_add",
    ),
    path(
        "customer-maintenance/sub-distributor/save/",
        sub_distributor_save,
        name="sub_distributor_save",
    ),
    path(
        "customer-maintenance/sub-distributor/<int:id>/update-subdist/",
        sub_distributor_update_subdist,
        name="sub_distributor_update_subdist",
    ),   
    path(
        "freight-cost/freightcost/",
        freight_cost_list,
        name="freight_cost_list",
    ),
    path(
        "freight-cost/freightcost/data/",
        freight_cost_data,
        name="freight_cost_data",
    ),
    path(
        "freight-cost/freightcost/export/",
        freight_cost_export,
        name="freight_cost_export",
    ),
    path(
        "freight-cost/freightcost/export-progress/",
        freight_cost_export_progress,
        name="freight_cost_export_progress",
    ),
    
    path(
        "warehouse-palettes/",
        include(
            ("apps.bom.urls.warehouse_palettes", "bom"), namespace="warehouse_palettes"
        ),
    ),
    
    path("branchstock_summary/", branchstock_summary, name="branchstock_summary"),
    path(
        "branchstocksummary/user/",
        branchstock_summary_user,
        name="branchstock_summary_user",
    ),
]
