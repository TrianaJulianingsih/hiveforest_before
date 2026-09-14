from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction

@login_required
def dash_arbalance(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Finance",
        feature="AR Balance Dashboard",
        description="User viewed the AR Balance dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiOTUwOThmYjAtMDZmYy00MDcyLTlmYTgtMWU3ODE2MDk0YjUwIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/arbalance_dashboard.html', context)
