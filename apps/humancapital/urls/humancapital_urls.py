from django.urls import path
from apps.base.views.autocomplete_view import autocomplete_view
from apps.humancapital.models.employee import Employee, EmployeeTitle
from apps.humancapital.models.structure import Organization, OrganizationType, Position
from apps.humancapital.views.employee_view import (
    List as EmpList, Create as EmpCreate, Ajax as EmpAjax, Detail as EmpDetail, Update as EmpUpdate, SoftDel as EmpSoftDel,
    batch_update as emp_batch_update, change_status as emp_change_status, quick_add as emp_quick_add)
from apps.humancapital.views.organization_view import (
    List as OrgList, Create as OrgCreate, Ajax as OrgAjax, Detail as OrgDetail, Update as OrgUpdate, SoftDel as OrgSoftDel,
    batch_update as org_batch_update, change_status as org_change_status, quick_add as org_quick_add)
from apps.humancapital.views.position_view import (
    List as PosList, Create as PosCreate, Ajax as PosAjax, Detail as PosDetail, Update as PosUpdate, SoftDel as PosSoftDel,
    batch_update as pos_batch_update, change_status as pos_change_status, quick_add as pos_quick_add,
    quick_rename as pos_quick_rename, VacantPositionAutocomplete as PosVacantAutocomplete)
from apps.humancapital.views.assignment_view import (
    List as AssList, Create as AssCreate, Ajax as AssAjax, Detail as AssDetail, Update as AssUpdate, SoftDel as AssSoftDel,
    batch_update as ass_batch_update, change_status as ass_change_status, quick_assign as ass_quick_assign,
    quick_assign_position as ass_quick_assign_position, quick_relocate as ass_quick_relocate)
from apps.humancapital.views.humancapital_view import landing as hcd_landing, organogram as hcd_organogram

app_name = 'humancapital'

urlpatterns = [
    # Landing page
    path('', hcd_landing, name='hcd-landing'),
    path('organogram/', hcd_organogram, name='organogram'),
    # Emnployee List paths
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
    # Others

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
    # Others

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
    # Others

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

    # Autocomplete views
    path('emp-autocomplete/', autocomplete_view(Employee).as_view(), name='emp-autocomplete'),
    path('emptitle-autocomplete/', autocomplete_view(EmployeeTitle).as_view(), name='emptitle-autocomplete'),
    path('orgtype-autocomplete/', autocomplete_view(OrganizationType).as_view(), name='orgtype-autocomplete'),
    path('org-autocomplete/', autocomplete_view(Organization).as_view(), name='org-autocomplete'),
    path('pos-autocomplete/', autocomplete_view(Position).as_view(), name='pos-autocomplete'),
    path('vacant-pos-autocomplete/', PosVacantAutocomplete.as_view(), name='vacant-pos-autocomplete'),

]