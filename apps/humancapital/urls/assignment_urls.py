from django.urls import path
from apps.humancapital.views.assignment_views import (
    List as AssList, Create as AssCreate, Ajax as AssAjax, Detail as AssDetail, Update as AssUpdate, SoftDel as AssSoftDel,
    batch_update as ass_batch_update, change_status as ass_change_status, quick_assign as ass_quick_assign,
    quick_relocate as ass_quick_relocate
)

urlpatterns = [
    # Assignment List Path
    path('assignment/', AssList.as_view(), name='assignment-list'),
    path('assignment/add/', AssCreate.as_view(), name='assignment-add'),
    path('assignment/ajax/', AssAjax.as_view(), name='assignment-ajax'),
    path('assignment/batch-update/', ass_batch_update, name='assignment-batch-udpate'),
    # Assignment CRUD paths
    path('assignment/<int:pk>/edit/', AssUpdate.as_view(), name='assignment-edit'),
    path('assignment/<int:pk>/detail/', AssDetail.as_view(), name='assignment-detail'),
    path('assignment/<int:pk>/change-status/', ass_change_status, name='assignment-change-status'),
    path('assignment/<int:pk>/soft-delete/', AssSoftDel.as_view(), name='assignment-soft-delete'),
    path('assignment/<int:pk>/quick-assign/', ass_quick_assign, name='assignment-quick-assign'),
    path('assignment/<int:pk>/quick-relocate/', ass_quick_relocate, name='assignment-quick-relocate'),
]
