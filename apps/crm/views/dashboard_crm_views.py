from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction

@login_required
def dash_hospital(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="CRM",
        feature="Hospital Dashboard",
        description="User viewed the Hospital dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiZDcwM2ExMTYtYjk1Ny00OGNmLTk4NmItOGFhYjNjYTZhNGRlIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/hospital_dashboard.html', context)

@login_required
def dash_doctor(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="CRM",
        feature="Doctor Dashboard",
        description="User viewed the Doctor dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiZTM1OTNmODQtNjg0ZS00YzRkLWE4OTctNTI4MGUwZWIxNmFlIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/doctor_dashboard.html', context)

