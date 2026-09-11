from django.urls import path
from apps.supplychain.views.autocompletes import BranchAutocomplete  # Import your custom view

urlpatterns = [
    path('branch-autocomplete/', BranchAutocomplete.as_view(), name='branch-autocomplete'),
]