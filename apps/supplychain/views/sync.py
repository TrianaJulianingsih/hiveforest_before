import os
import tempfile

from django.core.management import call_command
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@staff_member_required
def sync_stocks(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        user_id = request.user.id  # ✅ Get current logged-in user
        call_command('sync_stocks', cby=user_id)  # ✅ Pass user ID to the command
        return JsonResponse({'status': 'success', 'message': f'Stock sync completed by user {user_id}'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Sync failed: {str(e)}'}, status=500)


@csrf_exempt
@staff_member_required
def import_stftp(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    upload = request.FILES.get('file')
    if not upload:
        return JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)

    dry_run = request.POST.get('dry_run') in ('1', 'true', 'on')

    ext = os.path.splitext(upload.name)[1].lower() or '.csv'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        for chunk in upload.chunks():
            tmp.write(chunk)
        tmp.close()
        summary = call_command(
            'load_excel_stftp', file=tmp.name, cby=request.user.id, dry_run=dry_run
        )
        return JsonResponse({'status': 'success', 'message': summary})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Import failed: {str(e)}'}, status=500)
    finally:
        os.unlink(tmp.name)