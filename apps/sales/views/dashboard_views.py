from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction

@login_required
def sales_dashboard(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Sales",
        feature="Sales Dashboard",
        description="User viewed Sales PowerBI dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiMjU3Y2E4YmQtOTQ1My00OTYxLTgwNTItYjAwOTU1NjIwMmY5IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/sales_dashboard.html', context)

@login_required
def ecatalog_dashboard(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Sales",
        feature="E-Catalog Dashboard",
        description="User viewed E-Catalog PowerBI dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiNTYzMTBlYmYtNzJiNC00NTk2LWJiOGQtNjJlMTk4YzFhOWRiIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/ecatalog_dashboard.html', context)

@login_required
def iqvia_itma_dashboard(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="Sales",
        feature="IQVIA ITMA Dashboard",
        description="User viewed the IQVIA ITMA dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiNTYzMTBlYmYtNzJiNC00NTk2LWJiOGQtNjJlMTk4YzFhOWRiIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/iqvia_itma_dashboard.html', context)
