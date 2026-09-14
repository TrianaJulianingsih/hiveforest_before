from django.urls import path
from apps.cms.views.autocompletes_views import ModuleAutocomplete

urlpatterns = [
    path('module-autocomplete/', ModuleAutocomplete.as_view(), name='module-autocomplete'),
]