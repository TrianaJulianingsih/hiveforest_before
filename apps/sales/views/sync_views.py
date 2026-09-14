import os
import tempfile
import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.core.management.base import CommandError
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connection
import datetime
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


@csrf_exempt
# @staff_member_required
def sync_so(request):
    if request.method == 'POST':
        task_type = request.POST.get('type')
        dist_type = request.POST.get('dist')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        user_id = request.user.id if request.user.is_authenticated else None
        
        # Basic validation
        if not all([task_type, dist_type, start_date, end_date]):
            return JsonResponse({'success': False, 'message': 'All fields are required.'})

        # Validate date format
        try:
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'})

        sp_combine_so = {
            'mup': 'combine_so_rawmuso',
            'apl': 'combine_so_rawaplso',
            'app': 'combine_so_rawappso'
        }
        sp_update_so_price = 'update_so_price'
        sp_closed_so = 'closed_so'
        dist_id = {
            'mup': 1,
            'app': 9,
            'apl': 8
        }

        procedure_name = None
        try:
            with connection.cursor() as cursor:
                if task_type == 'combine_so':
                    procedure_name = sp_combine_so.get(dist_type)
                    if not procedure_name:
                        return JsonResponse({'success': False, 'message': 'Unknown dist type.'})
                    cursor.execute(f'CALL {procedure_name}(%s, %s, %s)', [start_date, end_date, user_id])
                elif task_type == 'update_so_price':
                    procedure_name = sp_update_so_price
                    dist = dist_id.get(dist_type)
                    if not dist:
                        return JsonResponse({'success': False, 'message': 'Unknown dist type.'})
                    cursor.execute(f'CALL {procedure_name}(%s, %s, %s, %s)', [dist, start_date, end_date, user_id])
                elif task_type == 'closed_so':
                    procedure_name = sp_closed_so
                    dist = dist_id.get(dist_type)
                    if not dist:
                        return JsonResponse({'success': False, 'message': 'Unknown dist type.'})
                    cursor.execute(f'CALL {procedure_name}(%s, %s, %s, %s)', [dist, start_date, end_date, user_id])
                else:
                    return JsonResponse({'success': False, 'message': 'Unknown type.'})
            msg = f'Sync successful for {procedure_name} from {start_date} to {end_date}'
            SystemLogService.log(
                request=request,
                action=LogAction.UPDATE,
                module="Sales",
                feature="Sync SO",
                description=msg,
                metadata={"task_type": task_type, "dist_type": dist_type, "start_date": start_date, "end_date": end_date},
                status="SUCCESS",
                log_type="SYSTEM",
            )
            return JsonResponse({'success': True, 'message': msg})
        except Exception as e:
            SystemLogService.log(
                request=request,
                action=LogAction.UPDATE,
                module="Sales",
                feature="Sync SO",
                description=f"Sync SO failed: {e}",
                status="FAILED",
                error_message=str(e),
                log_type="SYSTEM",
            )
            return JsonResponse({'success': False, 'message': f'Failed: {e}'})
    else:
        return JsonResponse({'success': False, 'message': 'Only POST requests are allowed.'})


@csrf_exempt
@staff_member_required
def import_rawappso(request):
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
    sheet = (request.POST.get('sheet') or 'Transaksi UBT').strip()

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
        if extension in {'.xlsx', '.xls'}:
            command_options['sheet'] = sheet

        summary = call_command('load_rawappso', **command_options)
        return JsonResponse(
            {
                'status': 'success',
                'message': summary or 'APP Selling Out import completed.',
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

