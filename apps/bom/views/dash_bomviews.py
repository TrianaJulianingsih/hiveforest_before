from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dash_distribution(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/distribution_dashboard.html', context)

@login_required
def dash_stock(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/stock_dashboard.html', context)
