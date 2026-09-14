import os
import tempfile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


@csrf_exempt
@staff_member_required
def sync_stocks(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user_id = request.user.id
        call_command('sync_stocks', cby=user_id)
        msg = f'Stock sync completed by user {user_id}'
        SystemLogService.log(
            request=request,
            action=LogAction.UPDATE,
            module="SupplyChain",
            feature="Sync Stocks",
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
            feature="Sync Stocks",
            description=f"Stock sync failed: {e}",
            status="FAILED",
            error_message=str(e),
            log_type="SYSTEM",
        )
        return JsonResponse({'status': 'error', 'message': f'Sync failed: {str(e)}'}, status=500)


@csrf_exempt
@staff_member_required
def import_stftp(request):
    if request.method != 'POST':
        return JsonResponse(
            {'status': 'error', 'message': 'Only POST requests are allowed.'},
            status=405,
        )

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse(
            {'status': 'error', 'message': 'No file uploaded.'},
            status=400,
        )

    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension not in {'.csv', '.xlsx', '.xls'}:
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Unsupported file format. Use CSV, XLSX, or XLS.',
            },
            status=400,
        )

    dry_run = request.POST.get('dry_run') in ('1', 'true', 'on')

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    try:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file.close()

        command_options = {
            'file': temp_file.name,
            'cby': request.user.id,
            'dry_run': dry_run,
        }

        summary = call_command('load_excel_stftp', **command_options)
        return JsonResponse(
            {
                'status': 'success',
                'message': summary or 'FTP Stock import completed.',
            }
        )
    except CommandError as error:
        return JsonResponse(
            {'status': 'error', 'message': str(error)},
            status=400,
        )
    except Exception as error:
        return JsonResponse(
            {'status': 'error', 'message': f'Import failed: {error}'},
            status=500,
        )
    finally:
        if not temp_file.closed:
            temp_file.close()
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
