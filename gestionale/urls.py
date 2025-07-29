# gestionale/urls.py
from django.urls import path
from .views import (
    AnagraficaListExportExcelView, AnagraficaListExportPdfView, AnagraficaPartitarioExportPdfView, DashboardView, AnagraficaListView, AnagraficaCreateView, 
    DipendenteDettaglioCreateView, AnagraficaUpdateView, AnagraficaDetailView,
    AnagraficaToggleAttivoView, DocumentoListExportExcelView, DocumentoListExportPdfView, 
    DocumentoListView, DocumentoDetailView, PagamentoDeleteView, PagamentoUpdateView, PrimaNotaCreateView, PrimaNotaListExportExcelView, PrimaNotaListExportPdfView, PrimaNotaListView,RegistraPagamentoView, SalvaAttivitaDiarioView, ScadenzarioExportPdfView,
    ScadenzarioListView, ScadenzarioExportExcelView, AnagraficaPartitarioExportExcelView,
    DashboardHRView, PrimaNotaCreateView, PrimaNotaUpdateView, PrimaNotaDeleteView, DocumentoDetailExportPdfView
)
from .views import documento_create_step1_testata, documento_create_step2_righe, documento_create_step3_scadenze, get_anagrafiche_by_tipo

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
    path('documenti/nuovo/step3/', documento_create_step3_scadenze, name='documento_create_step3_scadenze'),
    path('api/get-anagrafiche/', get_anagrafiche_by_tipo, name='api_get_anagrafiche'),
    path('anagrafiche/<int:pk>/', AnagraficaDetailView.as_view(), name='anagrafica_detail'),
    path('pagamenti/registra/', RegistraPagamentoView.as_view(), name='registra_pagamento'),
    path('scadenzario/', ScadenzarioListView.as_view(), name='scadenzario_list'),
    path('scadenzario/export/excel/', ScadenzarioExportExcelView.as_view(), name='scadenzario_export_excel'),
    path('scadenzario/export/pdf/', ScadenzarioExportPdfView.as_view(), name='scadenzario_export_pdf'),
    path('anagrafiche/<int:pk>/export/excel/', AnagraficaPartitarioExportExcelView.as_view(), name='anagrafica_partitario_export_excel'),
    path('anagrafiche/<int:pk>/export/pdf/', AnagraficaPartitarioExportPdfView.as_view(), name='anagrafica_partitario_export_pdf'),
    path('hr/', DashboardHRView.as_view(), name='dashboard_hr'),
    path('hr/<int:year>/<int:month>/<int:day>/', DashboardHRView.as_view(), name='dashboard_hr_data'),
    path('hr/salva-attivita/', SalvaAttivitaDiarioView.as_view(), name='salva_attivita_diario'),
    path('anagrafiche/export/excel/', AnagraficaListExportExcelView.as_view(), name='anagrafica_list_export_excel'),
    path('anagrafiche/export/pdf/', AnagraficaListExportPdfView.as_view(), name='anagrafica_list_export_pdf'),
    path('documenti/export/excel/', DocumentoListExportExcelView.as_view(), name='documento_list_export_excel'),
    path('documenti/export/pdf/', DocumentoListExportPdfView.as_view(), name='documento_list_export_pdf'),
    path('primanota/', PrimaNotaListView.as_view(), name='primanota_list'),
    path('primanota/nuovo/', PrimaNotaCreateView.as_view(), name='primanota_create'),
    path('primanota/<int:pk>/modifica/', PrimaNotaUpdateView.as_view(), name='primanota_update'),
    path('primanota/<int:pk>/elimina/', PrimaNotaDeleteView.as_view(), name='primanota_delete'),
    path('primanota/export/excel/', PrimaNotaListExportExcelView.as_view(), name='primanota_export_excel'),
    path('primanota/export/pdf/', PrimaNotaListExportPdfView.as_view(), name='primanota_export_pdf'),
    path('pagamenti/<int:pk>/elimina/', PagamentoDeleteView.as_view(), name='pagamento_delete'),
    path('pagamenti/<int:pk>/modifica/', PagamentoUpdateView.as_view(), name='pagamento_update'),
    path('documenti/<int:pk>/export/pdf/', DocumentoDetailExportPdfView.as_view(), name='documento_detail_export_pdf'),
]
