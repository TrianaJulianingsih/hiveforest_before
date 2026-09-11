from django.http import JsonResponse
from apps.supplychain.models import Branch, OrderType
from apps.base.models import SCMPermission
from apps.base.models.utils import get_permitted_branches, get_permitted_distributors
from django.contrib.auth.decorators import login_required

@login_required
def get_branches(request):
    distributor_id = request.GET.get('distributor_id')
    if distributor_id:
        permitted_distributors = get_permitted_distributors(request.user)
        if not permitted_distributors.filter(id=distributor_id).exists():
            return JsonResponse({'branches': []})  # Return empty if unauthorized
        # Fetch branches under the distributor and user's branch permissions
        branches = get_permitted_branches(request.user).filter(
            distributor_id=distributor_id,
            status=1
        )
        branch_data = [{'id': branch.id, 'name': branch.name} for branch in branches]
        return JsonResponse({'branches': branch_data})
    return JsonResponse({'branches': []})

@login_required
def get_ordertypes(request):
    distributor_id = request.GET.get('distributor_id')
    if distributor_id:
        permitted_distributors = get_permitted_distributors(request.user)
        if not permitted_distributors.filter(id=distributor_id).exists():
            return JsonResponse({'ordertypes': []})  # Return empty if unauthorized
        # Fetch branches under the distributor and user's branch permissions
        ordertypes = OrderType.objects.filter(
            distributor_id=distributor_id,
            status=1
        )
        ordertype_data = [{'id': ordertype.id, 'name': ordertype.name} for ordertype in ordertypes]
        return JsonResponse({'ordertypes': ordertype_data})
    return JsonResponse({'ordertypes': []})