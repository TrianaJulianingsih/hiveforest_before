from django.urls import include, path
from . import home_urls

urlpatterns = [
    path('', include(home_urls)),                   # Find home_urls.py
]