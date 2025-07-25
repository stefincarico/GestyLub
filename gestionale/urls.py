# gestionale/urls.py

from django.urls import path
# Importiamo la nuova vista
from .views import DashboardView, AnagraficaListView, AnagraficaCreateView, DipendenteDettaglioCreateView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('anagrafiche/', AnagraficaListView.as_view(), name='anagrafica_list'),
    path('anagrafiche/nuova/', AnagraficaCreateView.as_view(), name='anagrafica_create'),
    
    # NUOVO URL per il secondo step del dipendente.
    # Riceve l'ID dell'anagrafica come parametro.
    path('anagrafiche/<int:anagrafica_id>/dettagli-dipendente/', DipendenteDettaglioCreateView.as_view(), name='dipendente_dettaglio_create'),
]