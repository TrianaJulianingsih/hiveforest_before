from django.core.management import call_command
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: sync_arbalance                                      ║
# ║  Type: View                                                ║
# ║  Purpose: View for executing command from admin site       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\finance\views\sync.py                          ║
# ║  Created: Jun/23-2025 by Setiadji                          ║
# ║  Updates: Jun/28-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@csrf_exempt
@staff_member_required
def sync_arbalance(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        user_id = request.user.id  # ✅ Get current logged-in user
        call_command('sync_arbalance', cby=user_id)  # ✅ Pass user ID to the command
        
        # Log success
        SystemLogService.log(
            request=request,
            action=LogAction.SYSTEM,
            module="Finance",
            feature="AR Balance Sync",
            description=f"AR Balance sync completed successfully by user {request.user.username}.",
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return JsonResponse({'status': 'success', 'message': f'AR Balance sync completed by user {user_id}'})
    except Exception as e:
        # Log failure
        SystemLogService.error(
            request=request,
            module="Finance",
            feature="AR Balance Sync",
            error=e,
            description=f"AR Balance sync failed: {str(e)}"
        )
        return JsonResponse({'status': 'error', 'message': f'Sync failed: {str(e)}'}, status=500)
    
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: sync_arcollection                                   ║
# ║  Type: View                                                ║
# ║  Purpose: View for executing command from admin site       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\finance\views\sync.py                          ║
# ║  Created: Jun/27-2025 by Setiadji                          ║
# ║  Updates: Jun/27-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@csrf_exempt
@staff_member_required
def sync_arcollection(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        user_id = request.user.id  # ✅ Get current logged-in user
        call_command('sync_arcollection', cby=user_id)  # ✅ Pass user ID to the command
        
        # Log success
        SystemLogService.log(
            request=request,
            action=LogAction.SYSTEM,
            module="Finance",
            feature="AR Collection Sync",
            description=f"AR Collection sync completed successfully by user {request.user.username}.",
            status="SUCCESS",
            log_type="SYSTEM",
        )
        return JsonResponse({'status': 'success', 'message': f'AR Collection sync completed by user {user_id}'})   
    except Exception as e:
        # Log failure
        SystemLogService.error(
            request=request,
            module="Finance",
            feature="AR Collection Sync",
            error=e,
            description=f"AR Collection sync failed: {str(e)}"
        )
        return JsonResponse({'status': 'error', 'message': f'Sync failed: {str(e)}'}, status=500)
