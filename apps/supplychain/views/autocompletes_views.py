from dal import autocomplete
from django.db.models import Q
from apps.supplychain.models.distributions_models import Branch
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


class BranchAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Branch.objects.none()

        qs = Branch.objects.all()

        if self.q:
            qs = qs.filter(
                Q(name__icontains=self.q) | Q(name__istartswith=self.q)
            )

        qs = qs.order_by('name')

        SystemLogService.log(
            request=self.request,
            action=LogAction.READ,
            module="SupplyChain",
            feature="Branch Autocomplete",
            description=f"User searched branch autocomplete: '{self.q or ''}'",
            status="SUCCESS",
            log_type="SYSTEM",
        )

        return qs
