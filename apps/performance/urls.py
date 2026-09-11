from django.urls import path

from apps.performance import views
from apps.performance.master_views import (
    GroupAjax,
    GroupCreate,
    GroupList,
    GroupSoftDelete,
    GroupUpdate,
    ModelAjax,
    ModelCreate,
    ModelList,
    ModelSoftDelete,
    ModelUpdate,
    group_batch_update,
    group_change_status,
    model_batch_update,
    model_change_status,
)

app_name = "performance"

urlpatterns = [
    path("kpi/", views.kpi_dashboard, name="dashboard"),
    path("kpi/individual/", views.individual_view, name="individual"),
    path("kpi/import/", views.import_view, name="import"),
    path("kpi/periods/", views.period_list, name="period_list"),
    path("kpi/period/new/", views.period_manual_create, name="period_manual_create"),
    path("kpi/period/<int:pk>/edit/", views.period_manual_edit, name="period_manual_edit"),
    # Performance model CRUD (organization-style UI)
    path("kpi/models/", ModelList.as_view(), name="model_list"),
    path("kpi/models/ajax/", ModelAjax.as_view(), name="model_ajax"),
    path("kpi/models/add/", ModelCreate.as_view(), name="model_create"),
    path("kpi/models/batch-update/", model_batch_update, name="model_batch_update"),
    path("kpi/models/<int:pk>/edit/", ModelUpdate.as_view(), name="model_edit"),
    path("kpi/models/<int:pk>/change-status/", model_change_status, name="model_change_status"),
    path("kpi/models/<int:pk>/soft-delete/", ModelSoftDelete.as_view(), name="model_delete"),
    # Performance group CRUD (organization-style UI)
    path("kpi/groups/", GroupList.as_view(), name="group_list"),
    path("kpi/groups/ajax/", GroupAjax.as_view(), name="group_ajax"),
    path("kpi/groups/add/", GroupCreate.as_view(), name="group_create"),
    path("kpi/groups/batch-update/", group_batch_update, name="group_batch_update"),
    path("kpi/groups/<int:pk>/edit/", GroupUpdate.as_view(), name="group_edit"),
    path("kpi/groups/<int:pk>/change-status/", group_change_status, name="group_change_status"),
    path("kpi/groups/<int:pk>/soft-delete/", GroupSoftDelete.as_view(), name="group_delete"),
    # Legacy aliases
    path("kpi/model/new/", ModelCreate.as_view(), name="model_create_legacy"),
    path("kpi/group/new/", GroupCreate.as_view(), name="group_create_legacy"),
]
