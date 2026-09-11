from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def sales_dashboard(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiMjU3Y2E4YmQtOTQ1My00OTYxLTgwNTItYjAwOTU1NjIwMmY5IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/sales_dashboard.html', context)

@login_required
def ecatalog_dashboard(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiNTYzMTBlYmYtNzJiNC00NTk2LWJiOGQtNjJlMTk4YzFhOWRiIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/ecatalog_dashboard.html', context)

@login_required
def iqvia_itma_dashboard(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiNTYzMTBlYmYtNzJiNC00NTk2LWJiOGQtNjJlMTk4YzFhOWRiIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/iqvia_itma_dashboard.html', context)