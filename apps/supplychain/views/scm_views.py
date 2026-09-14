from django.http import JsonResponse
from apps.supplychain.models.distributions_models import Branch, OrderType
from apps.base.models import SCMPermission
from apps.base.models.utils import get_permitted_branches, get_permitted_distributors
from django.contrib.auth.decorators import login_required
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


@login_required
def get_branches(request):
    distributor_id = request.GET.get('distributor_id')
    if distributor_id:
        permitted_distributors = get_permitted_distributors(request.user)
        if not permitted_distributors.filter(id=distributor_id).exists():
            return JsonResponse({'branches': []})
        branches = get_permitted_branches(request.user).filter(
            distributor_id=distributor_id,
            status=1
        )
        branch_data = [{'id': branch.id, 'name': branch.name} for branch in branches]
        SystemLogService.log(
            request=request,
            action=LogAction.READ,
            module="SupplyChain",
            feature="Get Branches AJAX",
            description=f"User fetched branches for distributor {distributor_id}.",
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return JsonResponse({'branches': branch_data})
    return JsonResponse({'branches': []})


@login_required
def get_ordertypes(request):
    distributor_id = request.GET.get('distributor_id')
    if distributor_id:
        permitted_distributors = get_permitted_distributors(request.user)
        if not permitted_distributors.filter(id=distributor_id).exists():
            return JsonResponse({'ordertypes': []})
        ordertypes = OrderType.objects.filter(
            distributor_id=distributor_id,
            status=1
        )
        ordertype_data = [{'id': ordertype.id, 'name': ordertype.name} for ordertype in ordertypes]
        SystemLogService.log(
            request=request,
            action=LogAction.READ,
            module="SupplyChain",
            feature="Get Order Types AJAX",
            description=f"User fetched order types for distributor {distributor_id}.",
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return JsonResponse({'ordertypes': ordertype_data})
    return JsonResponse({'ordertypes': []})