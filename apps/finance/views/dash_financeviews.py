from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dash_arbalance(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiOTUwOThmYjAtMDZmYy00MDcyLTlmYTgtMWU3ODE2MDk0YjUwIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/arbalance_dashboard.html', context)