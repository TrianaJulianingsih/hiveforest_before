from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dash_mupstock(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiNjcwNTM2MjEtZjRlOC00YzlmLWE0YWMtYTNmNDI5YmNmZGE2IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/mupstock_dashboard.html', context)

@login_required
def dash_facdo(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiYjVlNWRkYzYtODM2Ni00MjQ4LTk2MDUtNjhjZTJhYzk3OWU2IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/facdo_dashboard.html', context)

@login_required
def dash_facstock(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiYWYxMjdjNjAtY2VjZC00OWUyLWEzN2UtNzY3Zjg1YTRhODMyIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/facstock_dashboard.html', context)

@login_required
def dash_distpo(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiNzRjNTMzYmEtZjMxZC00N2M5LWE3MmQtYmMxNTMyNjBjNWYzIiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/distpo_dashboard.html', context)

