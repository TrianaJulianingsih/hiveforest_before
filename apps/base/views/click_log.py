from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction

@csrf_exempt
@login_required
@require_POST
def log_click(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    
    module = data.get("module")
    feature = data.get("feature")
    description = data.get("description")
    metadata = data.get("metadata")
    
    if not module or not feature:
        return JsonResponse({"status": "error", "message": "Missing required fields: module and feature"}, status=400)
    
    SystemLogService.log(
        request=request,
        action=LogAction.CLICK,
        module=module,
        feature=feature,
        description=description,
        metadata=metadata
    )
    
    return JsonResponse({"status": "success"})
