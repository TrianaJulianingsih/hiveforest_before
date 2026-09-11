from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.cms.models.menusystem import MenuItem
from django.http import Http404


@login_required
def dashboard_views(request):
    menu_code = request.GET.get("menu")
    iframe_url = None
    if menu_code:
        menu = MenuItem.objects.filter(code=menu_code).first()
        if menu:
            iframe_url = menu.iframe_url
    if not iframe_url:
        iframe_url = ""
    context = {"iframe_url": iframe_url}
    return render(request, "bi/dashboard_views.html", context)
