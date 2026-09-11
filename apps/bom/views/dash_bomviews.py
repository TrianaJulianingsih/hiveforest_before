from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dash_distribution(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiYTIyMTgzMWQtMDMyMS00M2U1LWJkOWMtOThjMWY4N2I0YzIwIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/distribution_dashboard.html', context)

@login_required
def dash_stock(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiZTZlYTVmMjgtNzA0Zi00NmI2LWE1ZmMtNjc2NjA2NWYzYmQ3IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/stock_dashboard.html', context)