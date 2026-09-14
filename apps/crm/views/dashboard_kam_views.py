from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction

@login_required
def dash_kamactivity(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="CRM",
        feature="KAM Activity Dashboard",
        description="User viewed the KAM Activity dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiYzEwYWUxOTMtNGE3MS00MzA5LWFlNDgtY2I1YjBkMjc1NTA0IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/kamactivity_dashboard.html', context)

