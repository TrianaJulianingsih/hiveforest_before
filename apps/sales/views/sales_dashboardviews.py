from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def sales_dashboard(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/sales_dashboard.html', context)

@login_required
def ecatalog_dashboard(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/ecatalog_dashboard.html', context)

@login_required
def iqvia_itma_dashboard(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/iqvia_itma_dashboard.html', context)
