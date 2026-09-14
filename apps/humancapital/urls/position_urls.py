from django.urls import path
from apps.humancapital.views.position_views import (
    List as PosList, Create as PosCreate, Ajax as PosAjax, Detail as PosDetail, Update as PosUpdate, SoftDel as PosSoftDel,
    batch_update as pos_batch_update, change_status as pos_change_status, quick_add as pos_quick_add,
    quick_rename as pos_quick_rename
)
from apps.humancapital.views.assignment_views import quick_assign_position as ass_quick_assign_position

urlpatterns = [
    # Position List Path
    path('position/', PosList.as_view(), name='position-list'),
    path('position/add/', PosCreate.as_view(), name='position-add'),
    path('position/quick-add/', pos_quick_add, name='position-quick-add'),
    path('position/ajax/', PosAjax.as_view(), name='position-ajax'),
    path('position/batch-update/', pos_batch_update, name='position-batch-udpate'),
    # Position CRUD paths
    path('position/<int:pk>/edit/', PosUpdate.as_view(), name='position-edit'),
    path('position/<int:pk>/detail/', PosDetail.as_view(), name='position-detail'),
    path('position/<int:pk>/change-status/', pos_change_status, name='position-change-status'),
    path('position/<int:pk>/soft-delete/', PosSoftDel.as_view(), name='position-soft-delete'),
    path('position/<int:pk>/quick-rename/', pos_quick_rename, name='position-quick-rename'),
    path('position/<int:pk>/quick-assign/', ass_quick_assign_position, name='position-quick-assign'),
]
