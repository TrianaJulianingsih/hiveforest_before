from django.urls import path
from apps.humancapital.views.employee_views import (
    List as EmpList, Create as EmpCreate, Ajax as EmpAjax, Detail as EmpDetail, Update as EmpUpdate, SoftDel as EmpSoftDel,
    batch_update as emp_batch_update, change_status as emp_change_status, quick_add as emp_quick_add
)

urlpatterns = [
    # Employee List paths
    path('employee/', EmpList.as_view(), name='employee-list'),
    path('employee/add/', EmpCreate.as_view(), name='employee-add'),
    path('employee/quick-add/', emp_quick_add, name='employee-quick-add'),
    path('employee/ajax/', EmpAjax.as_view(), name='employee-ajax'),
    path('employee/batch-update/', emp_batch_update, name='employee-batch-udpate'),
    # Employee CRUD paths
    path('employee/<int:pk>/edit/', EmpUpdate.as_view(), name='employee-edit'),
    path('employee/<int:pk>/detail/', EmpDetail.as_view(), name='employee-detail'),
    path('employee/<int:pk>/change-status/', emp_change_status, name='employee-change-status'),
    path('employee/<int:pk>/soft-delete/', EmpSoftDel.as_view(), name='employee-soft-delete'),
]
