from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction


@login_required
def dash_mupstock(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="SupplyChain",
        feature="MUP Stock Dashboard",
        description="User accessed MUP Stock PowerBI Dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiNjcwNTM2MjEtZjRlOC00YzlmLWE0YWMtYTNmNDI5YmNmZGE2IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/mupstock_dashboard.html', context)


@login_required
def dash_facdo(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="SupplyChain",
        feature="Factory DO Dashboard",
        description="User accessed Factory DO PowerBI Dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiYjVlNWRkYzYtODM2Ni00MjQ4LTk2MDUtNjhjZTJhYzk3OWU2IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/facdo_dashboard.html', context)


@login_required
def dash_facstock(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="SupplyChain",
        feature="Factory Stock Dashboard",
        description="User accessed Factory Stock PowerBI Dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiYWYxMjdjNjAtY2VjZC00OWUyLWEzN2UtNzY3Zjg1YTRhODMyIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/facstock_dashboard.html', context)


@login_required
def dash_distpo(request):
    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="SupplyChain",
        feature="Distributor PO Dashboard",
        description="User accessed Distributor PO PowerBI Dashboard.",
        status="SUCCESS",
        log_type="SYSTEM",
    )
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiNzRjNTMzYmEtZjMxZC00N2M5LWE3MmQtYmMxNTMyNjBjNWYzIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/distpo_dashboard.html', context)
