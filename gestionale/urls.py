# gestionale/urls.py

from django.urls import path
from .views import DashboardView

urlpatterns = [
    # Questo è l'URL per la nostra dashboard.
    # Lo lasciamo come radice (stringa vuota) dell'app gestionale.
    # E gli diamo il nome 'dashboard' che risolve il nostro ultimo NoReverseMatch.
    path('', DashboardView.as_view(), name='dashboard'),
]