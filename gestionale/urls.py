# gestionale/urls.py
from django.urls import path
from .views import (
    DashboardView, AnagraficaListView, AnagraficaCreateView, 
    DipendenteDettaglioCreateView, AnagraficaUpdateView,
    AnagraficaToggleAttivoView, DocumentoListView, DocumentoDetailView
)
from .views import documento_create_step1_testata, documento_create_step2_righe

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('anagrafiche/', AnagraficaListView.as_view(), name='anagrafica_list'),
    path('anagrafiche/nuova/', AnagraficaCreateView.as_view(), name='anagrafica_create'),
    path('anagrafiche/<int:anagrafica_id>/dettagli-dipendente/', DipendenteDettaglioCreateView.as_view(), name='dipendente_dettaglio_create'),
    path('anagrafiche/<int:pk>/modifica/', AnagraficaUpdateView.as_view(), name='anagrafica_update'),
    path('anagrafiche/<int:pk>/toggle-attivo/', AnagraficaToggleAttivoView.as_view(), name='anagrafica_toggle_attivo'),
    path('documenti/', DocumentoListView.as_view(), name='documento_list'),
    path('documenti/<int:pk>/', DocumentoDetailView.as_view(), name='documento_detail'),
    path('documenti/nuovo/step1/', documento_create_step1_testata, name='documento_create_step1_testata'),
    path('documenti/nuovo/step2/', documento_create_step2_righe, name='documento_create_step2_righe'),
]