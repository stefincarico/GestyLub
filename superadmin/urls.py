# superadmin/urls.py
from django.urls import path
from .views import CompanyCreateView, CompanyDetailView, CompanyListView, CompanyUpdateView, DatabaseBackupView, SuperAdminDashboardView, UserCreateView, UserListView, UserPasswordChangeView, UserUpdateView

app_name = 'superadmin'
urlpatterns = [
    path('', SuperAdminDashboardView.as_view(), name='dashboard'),
    # URLS PER LE AZIENDE
    path('aziende/', CompanyListView.as_view(), name='company_list'),
    path('aziende/nuova/', CompanyCreateView.as_view(), name='company_create'),
    path('aziende/<int:pk>/modifica/', CompanyUpdateView.as_view(), name='company_update'),
    # URLS PER GLI UTENTI
    path('utenti/', UserListView.as_view(), name='user_list'),
    path('utenti/nuovo/', UserCreateView.as_view(), name='user_create'),
    path('utenti/<int:pk>/modifica/', UserUpdateView.as_view(), name='user_update'),
    path('utenti/<int:pk>/password/', UserPasswordChangeView.as_view(), name='user_password_change'),
    path('backup/', DatabaseBackupView.as_view(), name='database_backup'),
    path('aziende/<int:pk>/', CompanyDetailView.as_view(), name='company_detail'),
]