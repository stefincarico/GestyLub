# gestionale/urls.py

from django.urls import path
# Importiamo la nuova vista
from .views import DashboardView, AnagraficaListView, AnagraficaCreateView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('anagrafiche/', AnagraficaListView.as_view(), name='anagrafica_list'),
    
    # NUOVO URL per la creazione delle anagrafiche
    path('anagrafiche/nuova/', AnagraficaCreateView.as_view(), name='anagrafica_create'),
]