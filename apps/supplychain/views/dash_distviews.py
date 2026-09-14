from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dash_mupstock(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/mupstock_dashboard.html', context)

@login_required
def dash_facdo(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/facdo_dashboard.html', context)

@login_required
def dash_facstock(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/facstock_dashboard.html', context)

@login_required
def dash_distpo(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/distpo_dashboard.html', context)

