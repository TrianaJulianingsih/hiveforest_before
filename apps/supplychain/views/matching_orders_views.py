from django.core.management import call_command
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


@csrf_exempt
@staff_member_required
def matching_orders(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user_id = request.user.id
        call_command('matching_orders', uby=user_id)
        msg = f'Matching order completed by user {user_id}'
        SystemLogService.log(
            request=request,
            action=LogAction.UPDATE,
            module="SupplyChain",
            feature="Matching Orders",
            description=msg,
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return JsonResponse({'status': 'success', 'message': msg})
    except Exception as e:
        SystemLogService.log(
            request=request,
            action=LogAction.UPDATE,
            module="SupplyChain",
            feature="Matching Orders",
            description=f"Matching order failed: {e}",
            status="FAILED",
            error_message=str(e),
            log_type="SYSTEM",
        )
        return JsonResponse({'status': 'error', 'message': f'Matching order failed: {str(e)}'}, status=500)
