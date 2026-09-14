from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


@login_required
def dash_distribution(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="BOM",
        feature="Distribution Dashboard",
        description="User viewed the Distribution dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiYTIyMTgzMWQtMDMyMS00M2U1LWJkOWMtOThjMWY4N2I0YzIwIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/distribution_dashboard.html', context)


@login_required
def dash_stock(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="BOM",
        feature="Stock Dashboard",
        description="User viewed the Stock dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiZTZlYTVmMjgtNzA0Zi00NmI2LWE1ZmMtNjc2NjA2NWYzYmQ3IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/stock_dashboard.html', context)