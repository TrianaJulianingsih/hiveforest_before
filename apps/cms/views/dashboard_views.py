from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.cms.models.menu_system_models import MenuItem
from django.http import Http404


@login_required
def dashboard_views(request):
    from apps.base.services.system_log_service import SystemLogService
    from apps.base.models.system_log import LogAction

    menu_code = request.GET.get("menu")
    iframe_url = None
    feature_name = "CMS Dashboard"
    description_text = "User viewed a CMS dashboard."

    if menu_code:
        menu = MenuItem.objects.filter(code=menu_code).first()
        if menu:
            iframe_url = menu.iframe_url
            feature_name = f"Dashboard: {menu.name}"
            description_text = f"User viewed the '{menu.name}' CMS dashboard."

    SystemLogService.log(
        request=request,
        action=LogAction.READ,
        module="CMS",
        feature=feature_name,
        description=description_text,
        status="SUCCESS",
        log_type="SYSTEM",
    )

    if not iframe_url:
        iframe_url = ""
    context = {"iframe_url": iframe_url}
    return render(request, "bi/dashboard_views.html", context)
