# superadmin/urls.py
from django.urls import path
from .views import SuperAdminDashboardView

app_name = 'superadmin'
urlpatterns = [
    path('', SuperAdminDashboardView.as_view(), name='dashboard'),
]