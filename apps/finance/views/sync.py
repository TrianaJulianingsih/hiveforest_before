from django.core.management import call_command
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt

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
        return JsonResponse({'status': 'success', 'message': f'AR Balance sync completed by user {user_id}'})
    except Exception as e:
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
        return JsonResponse({'status': 'success', 'message': f'AR Collection sync completed by user {user_id}'})   
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Sync failed: {str(e)}'}, status=500)
