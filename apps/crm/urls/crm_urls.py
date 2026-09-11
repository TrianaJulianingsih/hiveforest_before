from django.urls import include, path
from apps.crm.views.dash_kamviews import dash_kamactivity
from apps.crm.views.dash_crmviews import dash_hospital, dash_doctor
app_name = 'crm'  # Optional: Namespace for the app

urlpatterns = [
    path('bi/dashboard/kamactivity/', dash_kamactivity, name='dash_kamactivity'),
    path('bi/dashboard/hospital/', dash_hospital, name='dash_hospital'),
    path('bi/dashboard/doctor/', dash_doctor, name='dash_doctor'),
    path('dashboard/', include('apps.crm.urls.dashboard_urls')),
]