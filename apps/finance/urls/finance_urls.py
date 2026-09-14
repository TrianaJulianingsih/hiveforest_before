from django.urls import path
from apps.finance.views.sync_views import sync_arbalance, sync_arcollection
from apps.finance.views.dashboard_finance_views import dash_arbalance
app_name = 'finance'

urlpatterns = [
    path('sync/arbalance/', sync_arbalance, name='sync_arbalance'),
    path('sync/arcollection/', sync_arcollection, name='sync_arcollection'),
    path('bi/dashboard/arbalance/', dash_arbalance, name='dash_arbalance'),
]