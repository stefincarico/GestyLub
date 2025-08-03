# superadmin/urls.py
from django.urls import path
from .views import CompanyCreateView, CompanyListView, CompanyUpdateView, SuperAdminDashboardView

app_name = 'superadmin'
urlpatterns = [
    path('', SuperAdminDashboardView.as_view(), name='dashboard'),
    # URLS PER LE AZIENDE
    path('aziende/', CompanyListView.as_view(), name='company_list'),
    path('aziende/nuova/', CompanyCreateView.as_view(), name='company_create'),
    path('aziende/<int:pk>/modifica/', CompanyUpdateView.as_view(), name='company_update'),
]