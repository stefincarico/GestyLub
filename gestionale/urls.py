# gestionale/urls.py
from django.urls import path
from .views import (
    AdminDashboardView, AliquotaIVACreateView, AliquotaIVAListView, AliquotaIVAToggleAttivoView, AliquotaIVAUpdateView, AnagraficaListExportExcelView, AnagraficaListExportPdfView, AnagraficaPartitarioExportPdfView, CausaleCreateView, CausaleListView, CausaleToggleAttivoView, CausaleUpdateView, ContoFinanziarioCreateView, ContoFinanziarioListView, ContoFinanziarioToggleAttivoView, ContoFinanziarioUpdateView, ContoOperativoCreateView, ContoOperativoListView, ContoOperativoToggleAttivoView, ContoOperativoUpdateView, DashboardView, AnagraficaListView, AnagraficaCreateView, DipendenteDetailView, 
    DipendenteDettaglioCreateView, AnagraficaUpdateView, AnagraficaDetailView,
    AnagraficaToggleAttivoView, DocumentoListExportExcelView, DocumentoListExportPdfView, 
    DocumentoListView, DocumentoDetailView, ExportTabelleContabiliView, ExportTabelleSistemaView, MezzoAziendaleCreateView, MezzoAziendaleListView, MezzoAziendaleToggleAttivoView, MezzoAziendaleUpdateView, ModalitaPagamentoCreateView, ModalitaPagamentoListView, ModalitaPagamentoToggleAttivoView, ModalitaPagamentoUpdateView, PagamentoDeleteView, PagamentoUpdateView, PrimaNotaCreateView, PrimaNotaListExportExcelView, PrimaNotaListExportPdfView, PrimaNotaListView,RegistraPagamentoView, SalvaAttivitaDiarioView, ScadenzaPersonaleCreateView, ScadenzaPersonaleDeleteView, ScadenzaPersonaleUpdateView, ScadenzarioExportPdfView,
    ScadenzarioListView, ScadenzarioExportExcelView, AnagraficaPartitarioExportExcelView,
    DashboardHRView, PrimaNotaCreateView, PrimaNotaUpdateView, PrimaNotaDeleteView, DocumentoDetailExportPdfView, TesoreriaDashboardView, TesoreriaExportExcelView, TesoreriaExportPdfView, TipoScadenzaPersonaleCreateView, TipoScadenzaPersonaleListView, TipoScadenzaPersonaleToggleAttivoView, TipoScadenzaPersonaleUpdateView
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
    path('tesoreria/', TesoreriaDashboardView.as_view(), name='tesoreria_dashboard'),
    path('tesoreria/export/excel/', TesoreriaExportExcelView.as_view(), name='tesoreria_export_excel'),
    path('tesoreria/export/pdf/', TesoreriaExportPdfView.as_view(), name='tesoreria_export_pdf'),
    path('admin-panel/', AdminDashboardView.as_view(), name='admin_dashboard'),
    # URLS PER MODALITA' DI PAGAMENTO
    path('admin-panel/modalita-pagamento/', ModalitaPagamentoListView.as_view(), name='modalita_pagamento_list'),
    path('admin-panel/modalita-pagamento/nuova/', ModalitaPagamentoCreateView.as_view(), name='modalita_pagamento_create'),
    path('admin-panel/modalita-pagamento/<int:pk>/modifica/', ModalitaPagamentoUpdateView.as_view(), name='modalita_pagamento_update'),
    path('admin-panel/modalita-pagamento/<int:pk>/toggle-attivo/', ModalitaPagamentoToggleAttivoView.as_view(), name='modalita_pagamento_toggle'),
    # URLS PER ALIQUOTE IVA
    path('admin-panel/aliquote-iva/', AliquotaIVAListView.as_view(), name='aliquota_iva_list'),
    path('admin-panel/aliquote-iva/nuova/', AliquotaIVACreateView.as_view(), name='aliquota_iva_create'),
    path('admin-panel/aliquote-iva/<int:pk>/modifica/', AliquotaIVAUpdateView.as_view(), name='aliquota_iva_update'),
    path('admin-panel/aliquote-iva/<int:pk>/toggle-attivo/', AliquotaIVAToggleAttivoView.as_view(), name='aliquota_iva_toggle'),
    # URLS PER CAUSALI CONTABILI
    path('admin-panel/causali/', CausaleListView.as_view(), name='causale_list'),
    path('admin-panel/causali/nuova/', CausaleCreateView.as_view(), name='causale_create'),
    path('admin-panel/causali/<int:pk>/modifica/', CausaleUpdateView.as_view(), name='causale_update'),
    path('admin-panel/causali/<int:pk>/toggle-attivo/', CausaleToggleAttivoView.as_view(), name='causale_toggle'),
        # URLS PER CONTI FINANZIARI
    path('admin-panel/conti-finanziari/', ContoFinanziarioListView.as_view(), name='conto_finanziario_list'),
    path('admin-panel/conti-finanziari/nuovo/', ContoFinanziarioCreateView.as_view(), name='conto_finanziario_create'),
    path('admin-panel/conti-finanziari/<int:pk>/modifica/', ContoFinanziarioUpdateView.as_view(), name='conto_finanziario_update'),
    path('admin-panel/conti-finanziari/<int:pk>/toggle-attivo/', ContoFinanziarioToggleAttivoView.as_view(), name='conto_finanziario_toggle'),
    # URLS PER CONTI OPERATIVI
    path('admin-panel/conti-operativi/', ContoOperativoListView.as_view(), name='conto_operativo_list'),
    path('admin-panel/conti-operativi/nuovo/', ContoOperativoCreateView.as_view(), name='conto_operativo_create'),
    path('admin-panel/conti-operativi/<int:pk>/modifica/', ContoOperativoUpdateView.as_view(), name='conto_operativo_update'),
    path('admin-panel/conti-operativi/<int:pk>/toggle-attivo/', ContoOperativoToggleAttivoView.as_view(), name='conto_operativo_toggle'),
    # URLS PER MEZZI AZIENDALI
    path('admin-panel/mezzi/', MezzoAziendaleListView.as_view(), name='mezzo_aziendale_list'),
    path('admin-panel/mezzi/nuovo/', MezzoAziendaleCreateView.as_view(), name='mezzo_aziendale_create'),
    path('admin-panel/mezzi/<int:pk>/modifica/', MezzoAziendaleUpdateView.as_view(), name='mezzo_aziendale_update'),
    path('admin-panel/mezzi/<int:pk>/toggle-attivo/', MezzoAziendaleToggleAttivoView.as_view(), name='mezzo_aziendale_toggle'),
    # URLS PER TIPI SCADENZE PERSONALE
    path('admin-panel/tipi-scadenze/', TipoScadenzaPersonaleListView.as_view(), name='tipo_scadenza_personale_list'),
    path('admin-panel/tipi-scadenze/nuovo/', TipoScadenzaPersonaleCreateView.as_view(), name='tipo_scadenza_personale_create'),
    path('admin-panel/tipi-scadenze/<int:pk>/modifica/', TipoScadenzaPersonaleUpdateView.as_view(), name='tipo_scadenza_personale_update'),
    path('admin-panel/tipi-scadenze/<int:pk>/toggle-attivo/', TipoScadenzaPersonaleToggleAttivoView.as_view(), name='tipo_scadenza_personale_toggle'),
    # NUOVO URL SPECIFICO PER IL FASCICOLO
    path('dipendenti/<int:pk>/', DipendenteDetailView.as_view(), name='dipendente_detail'),
    # NUOVI URL PER CRUD SCADENZE PERSONALI
    path('dipendenti/<int:dipendente_pk>/scadenze/nuova/', ScadenzaPersonaleCreateView.as_view(), name='scadenza_personale_create'),
    path('dipendenti/scadenze/<int:pk>/modifica/', ScadenzaPersonaleUpdateView.as_view(), name='scadenza_personale_update'),
    path('dipendenti/scadenze/<int:pk>/elimina/', ScadenzaPersonaleDeleteView.as_view(), name='scadenza_personale_delete'),
    # NUOVO URL PER EXPORT DI SISTEMA
    path('admin-panel/export-sistema/', ExportTabelleSistemaView.as_view(), name='export_tabelle_sistema'),
    path('admin-panel/export-contabili/', ExportTabelleContabiliView.as_view(), name='export_tabelle_contabili'),
]
