from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.cms.models.menusystem import MenuItem

@login_required
def home(request):

    # menus = MenuItem.objects.prefetch_related('children')
    menus = MenuItem.objects.filter(parent__isnull=True)
    return render(request, 'home.html', {'menus': menus}) 
