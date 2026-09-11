from django.urls import path
from apps.base.views.home import home

urlpatterns = [
    path('', home, name='home'),
]