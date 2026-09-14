from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dash_kamactivity(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/kamactivity_dashboard.html', context)
