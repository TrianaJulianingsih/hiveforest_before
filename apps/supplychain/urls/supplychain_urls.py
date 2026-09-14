from django.urls import path
from apps.supplychain.views.order_views import (
    order_list,
    order_add,
    order_edit,
    order_view,
    order_details,
)
from apps.supplychain.views.scm_views import get_branches, get_ordertypes
from apps.supplychain.views.dash_dist_views import (
    dash_mupstock,
    dash_facdo,
    dash_distpo,
    dash_facstock,
)
from apps.supplychain.views.matching_orders_views import matching_orders
from apps.supplychain.views.sync_views import sync_stocks, import_stftp
from apps.supplychain.views.branch_views import (
    BranchCreateView,
    BranchDeleteView,
    BranchListView,
    BranchUpdateView,
)

app_name = "supplychain"

urlpatterns = [
    path("sync/stocks", sync_stocks, name="sync_stocks"),
    path("import/stftp", import_stftp, name="import_stftp"),
    path("matching-orders/", matching_orders, name="matching_orders"),
    path("orders/", order_list, name="order_list"),
    path("orders/add/", order_add, name="order_add"),
    path("orders/edit/<int:pk>/", order_edit, name="order_edit"),
    path("orders/view/<int:pk>/", order_view, name="order_view"),
    path("orders/details/<int:pk>/", order_details, name="order_details"),
    path("get-branches/", get_branches, name="get_branches"),
    path("get-ordertypes/", get_ordertypes, name="get_ordertypes"),
    path("bi/dashboard/mupstock/", dash_mupstock, name="dash_mupstock"),
    path("bi/dashboard/facdo/", dash_facdo, name="dash_facdo"),
    path("bi/dashboard/facstock/", dash_facstock, name="dash_facstock"),
    path("bi/dashboard/distpo/", dash_distpo, name="dash_distpo"),
    # Branch Module URLs
    path("distribution/branches/", BranchListView.as_view(), name="branch_list"),
    path("distribution/branches/add/", BranchCreateView.as_view(), name="branch_add"),
    path(
        "distribution/branches/<int:pk>/edit/",
        BranchUpdateView.as_view(),
        name="branch_edit",
    ),
    path(
        "distribution/branches/<int:pk>/delete/",
        BranchDeleteView.as_view(),
        name="branch_delete",
    ),
]
