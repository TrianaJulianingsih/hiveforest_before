from dal import autocomplete
from django.db.models import Q
from apps.cms.models.module_managers_models import ModuleList

class ModuleAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Ensure the user has the correct permissions
        if not self.request.user.is_authenticated:
            return ModuleList.objects.none()

        qs = ModuleList.objects.all()

        # Apply search query with icontains or istartswith
        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q) |
                Q(name__istartswith=self.q) |
                Q(application__icountains=self.q) |
                Q(application__istartswith=self.q) 
            )

        # Ensure consistent ordering to avoid UnorderedObjectListWarning
        qs = qs.order_by('name')  # Replace 'name' with the field to order by

        return qs