from django.urls import path
from apps.humancapital.views.humancapital_views import landing as hcd_landing, organogram as hcd_organogram
from .employee_urls import urlpatterns as employee_patterns
from .organization_urls import urlpatterns as organization_patterns
from .position_urls import urlpatterns as position_patterns
from .assignment_urls import urlpatterns as assignment_patterns
from .autocomplete_urls import urlpatterns as autocomplete_patterns

app_name = 'humancapital'

urlpatterns = [
    # Landing page
    path('', hcd_landing, name='hcd-landing'),
    path('organogram/', hcd_organogram, name='organogram'),
] + employee_patterns + organization_patterns + position_patterns + assignment_patterns + autocomplete_patterns