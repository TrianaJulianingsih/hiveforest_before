from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dash_hospital(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/hospital_dashboard.html', context)

@login_required
def dash_doctor(request):
    context = {
        'iframe_url': ''
    }
    return render(request, 'bi/doctor_dashboard.html', context)