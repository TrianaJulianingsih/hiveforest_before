from django.urls import path
from apps.base.views.autocomplete_view import autocomplete_view
from apps.humancapital.models.employee_models import Employee, EmployeeTitle
from apps.humancapital.models.structure_models import Organization, OrganizationType, Position
from apps.humancapital.views.position_views import VacantPositionAutocomplete as PosVacantAutocomplete

urlpatterns = [
    # Autocomplete views
    path('emp-autocomplete/', autocomplete_view(Employee).as_view(), name='emp-autocomplete'),
    path('emptitle-autocomplete/', autocomplete_view(EmployeeTitle).as_view(), name='emptitle-autocomplete'),
    path('orgtype-autocomplete/', autocomplete_view(OrganizationType).as_view(), name='orgtype-autocomplete'),
    path('org-autocomplete/', autocomplete_view(Organization).as_view(), name='org-autocomplete'),
    path('pos-autocomplete/', autocomplete_view(Position).as_view(), name='pos-autocomplete'),
    path('vacant-pos-autocomplete/', PosVacantAutocomplete.as_view(), name='vacant-pos-autocomplete'),
]
