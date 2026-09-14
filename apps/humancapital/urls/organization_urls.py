from django.urls import path
from apps.humancapital.views.organization_views import (
    List as OrgList, Create as OrgCreate, Ajax as OrgAjax, Detail as OrgDetail, Update as OrgUpdate, SoftDel as OrgSoftDel,
    batch_update as org_batch_update, change_status as org_change_status, quick_add as org_quick_add
)

urlpatterns = [
    # Organization List Path
    path('organization/', OrgList.as_view(), name='organization-list'),
    path('organization/add/', OrgCreate.as_view(), name='organization-add'),
    path('organization/quick-add/', org_quick_add, name='organization-quick-add'),
    path('organization/ajax/', OrgAjax.as_view(), name='organization-ajax'),
    path('organization/batch-update/', org_batch_update, name='organization-batch-udpate'),
    # Organization CRUD paths
    path('organization/<int:pk>/edit/', OrgUpdate.as_view(), name='organization-edit'),
    path('organization/<int:pk>/detail/', OrgDetail.as_view(), name='organization-detail'),
    path('organization/<int:pk>/change-status/', org_change_status, name='organization-change-status'),
    path('organization/<int:pk>/soft-delete/', OrgSoftDel.as_view(), name='organization-soft-delete'),
]
