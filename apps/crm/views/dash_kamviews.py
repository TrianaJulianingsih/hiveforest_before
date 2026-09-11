from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dash_kamactivity(request):
    context = {
        'iframe_url': 'https://app.powerbi.com/view?r=eyJrIjoiYzEwYWUxOTMtNGE3MS00MzA5LWFlNDgtY2I1YjBkMjc1NTA0IiwidCI6IjhiYTkzMWVjLTQwZDUtNDQwNi1hOGE3LTcyMDZmODRkYmQ1ZCIsImMiOjEwfQ%3D%3D'
    }
    return render(request, 'bi/kamactivity_dashboard.html', context)
