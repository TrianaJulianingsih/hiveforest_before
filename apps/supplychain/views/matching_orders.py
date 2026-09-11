from django.core.management import call_command
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@staff_member_required
def matching_orders(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user_id = request.user.id  # ✅ Get current logged-in user
        call_command('matching_orders', uby=user_id)  # ✅ Pass user ID to the command
        return JsonResponse({'status': 'success', 'message': f'Matching order completed by user {user_id}'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Matching order failed: {str(e)}'}, status=500)