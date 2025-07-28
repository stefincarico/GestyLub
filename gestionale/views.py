# gestionale/views.py

# ==============================================================================
# === IMPORTAZIONI ORGANIZZATE                                              ===
# ==============================================================================
# Standard Library
from dataclasses import field
import json
from datetime import date, timedelta
today = date.today()
from decimal import Decimal

# Django Core
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView,DeleteView

# Librerie di terze parti
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from weasyprint import HTML

# Importazioni delle app locali
from .forms import (
    AnagraficaForm, DiarioAttivitaForm, DipendenteDettaglioForm,
    DocumentoFilterForm, DocumentoRigaForm, DocumentoTestataForm,
    PagamentoForm, PartitarioFilterForm, PrimaNotaFilterForm, PrimaNotaForm,
    ScadenzarioFilterForm, ScadenzaWizardForm,PrimaNotaUpdateForm
)
from .models import (
    AliquotaIVA, Anagrafica, Cantiere, Causale, ContoFinanziario,
    ContoOperativo, DiarioAttivita, DipendenteDettaglio, DocumentoRiga,
    DocumentoTestata, MezzoAziendale, ModalitaPagamento, PrimaNota, Scadenza
)
from .report_utils import generate_excel_report, generate_pdf_report


# ==============================================================================
# === MIXINS E FUNZIONI HELPER GLOBALI                                      ===
# ==============================================================================

class TenantRequiredMixin(LoginRequiredMixin, View):
    """Mixin per assicurare che un tenant sia attivo in sessione."""
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('active_tenant_id'):
            return redirect(reverse('tenant_selection'))
        return super().dispatch(request, *args, **kwargs)

def clear_doc_wizard_session(session):
    """Pulisce i dati del wizard dalla sessione."""
    session.pop('doc_testata_data', None)
    session.pop('doc_righe_data', None)
    session.pop('doc_scadenze_data', None)


# ==============================================================================
# === VISTE PRINCIPALI, ANAGRAFICHE E DOCUMENTI                             ===
# ==============================================================================

class DashboardView(TenantRequiredMixin, View):
    """Mostra la dashboard principale."""
    def get(self, request, *args, **kwargs):
        active_tenant_name = request.session.get('active_tenant_name')
        user_company_role = request.session.get('user_company_role')
        context = {'active_tenant_name': active_tenant_name, 'user_company_role': user_company_role}
        return render(request, 'gestionale/dashboard.html', context)

class AnagraficaListView(TenantRequiredMixin, ListView):
    """Mostra l'elenco paginato delle anagrafiche."""
    model = Anagrafica
    template_name = 'gestionale/anagrafica_list.html'
    context_object_name = 'anagrafiche'
    paginate_by = 15

class AnagraficaCreateView(TenantRequiredMixin, CreateView):
    # ... (codice invariato) ...
    model = Anagrafica
    form_class = AnagraficaForm
    template_name = 'gestionale/anagrafica_form.html'

    def get_success_url(self):
        if self.object.tipo == Anagrafica.Tipo.DIPENDENTE:
            return reverse('dipendente_dettaglio_create', kwargs={'anagrafica_id': self.object.pk})
        else:
            return reverse('anagrafica_list')

    def form_valid(self, form):
        """
        Ora questo metodo deve solo impostare i campi utente e lasciare
        che il modello si occupi del resto.
        """
        # Otteniamo l'oggetto senza salvarlo
        anagrafica = form.save(commit=False)
        
        # Impostiamo l'utente
        anagrafica.created_by = self.request.user
        anagrafica.updated_by = self.request.user
        
        # Salviamo. Il metodo save() personalizzato del modello Anagrafica
        # verrà chiamato automaticamente e genererà il codice.
        anagrafica.save()
        
        # Assegniamo l'oggetto alla vista per il reindirizzamento
        self.object = anagrafica
        
        return HttpResponseRedirect(self.get_success_url())

class AnagraficaUpdateView(TenantRequiredMixin, UpdateView):
    # ... (codice invariato) ...
    model = Anagrafica
    form_class = AnagraficaForm
    template_name = 'gestionale/anagrafica_form.html'
    success_url = reverse_lazy('anagrafica_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class AnagraficaToggleAttivoView(TenantRequiredMixin, View):
    # ... (codice invariato) ...
    def post(self, request, *args, **kwargs):
        anagrafica = get_object_or_404(Anagrafica, pk=kwargs.get('pk'))
        anagrafica.attivo = not anagrafica.attivo
        anagrafica.updated_by = request.user
        anagrafica.save()
        return redirect('anagrafica_list')

class DipendenteDettaglioCreateView(TenantRequiredMixin, CreateView):
    # ... (codice invariato) ...
    model = DipendenteDettaglio
    form_class = DipendenteDettaglioForm
    template_name = 'gestionale/dipendente_dettaglio_form.html'
    success_url = reverse_lazy('anagrafica_list')
    def dispatch(self, request, *args, **kwargs):
        self.anagrafica = get_object_or_404(Anagrafica, pk=kwargs['anagrafica_id'], tipo=Anagrafica.Tipo.DIPENDENTE)
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['anagrafica'] = self.anagrafica
        return context
    def form_valid(self, form):
        dettaglio = form.save(commit=False)
        dettaglio.anagrafica = self.anagrafica
        dettaglio.save()
        self.object = dettaglio
        return HttpResponseRedirect(self.get_success_url())

# ==============================================================================
# === VISTE WIZARD CREAZIONE DOCUMENTO                                      ===
# ==============================================================================

@login_required
def documento_create_step1_testata(request):
    """
    Step 1 del wizard: inserimento dati della testata.
    """
    if request.method == 'POST':
        form = DocumentoTestataForm(request.POST)
        if form.is_valid():
            request.session['doc_testata_data'] = {
                'tipo_doc': form.cleaned_data['tipo_doc'],
                'anagrafica_id': form.cleaned_data['anagrafica'].pk,
                'data_documento': form.cleaned_data['data_documento'].isoformat(),
                'modalita_pagamento_id': form.cleaned_data['modalita_pagamento'].pk,
                'cantiere_id': form.cleaned_data['cantiere'].pk if form.cleaned_data['cantiere'] else None,
                'note': form.cleaned_data['note'],
                'numero_documento_manuale': form.cleaned_data.get('numero_documento_manuale'),
            }
            request.session.pop('doc_righe_data', None)
            request.session.pop('doc_scadenze_data', None)
            return redirect(reverse('documento_create_step2_righe'))
    else:
        form = DocumentoTestataForm()

    # Definiamo la lista di tipi passivi e la passiamo al template come JSON
    tipi_passivi = [
        DocumentoTestata.TipoDoc.FATTURA_ACQUISTO, 
        DocumentoTestata.TipoDoc.NOTA_CREDITO_ACQUISTO
    ]
    
    context = {
        'form': form,
        'tipi_passivi_json': json.dumps(tipi_passivi) # Converte la lista Python in una stringa JSON
    }
    return render(request, 'gestionale/documento_create_step1.html', context)

@login_required
def documento_create_step2_righe(request):
    """
    Step 2 del wizard: inserimento delle righe del documento.
    """
    testata_data = request.session.get('doc_testata_data')
    # Se per qualche motivo mancano i dati del passo 1, torna all'inizio.
    if not testata_data:
        return redirect(reverse('documento_create_step1_testata'))

    righe_data = request.session.get('doc_righe_data', [])
    # === NUOVA LOGICA DI ELIMINAZIONE RIGA (GESTITA CON GET) ===
    riga_da_eliminare_idx = request.GET.get('delete_riga')
    if riga_da_eliminare_idx is not None:
        try:
        # Rimuoviamo la riga dalla lista usando il suo indice
            righe_data.pop(int(riga_da_eliminare_idx))
            request.session['doc_righe_data'] = righe_data
            messages.success(request, "Riga eliminata con successo.")
        except (ValueError, IndexError):
            messages.error(request, "Errore durante l'eliminazione della riga.")
        # Reindirizziamo per pulire l'URL dal parametro 'delete_riga'
        return redirect(reverse('documento_create_step2_righe'))


    if request.method == 'POST':
        # Controlliamo se l'utente vuole andare al passo 3
        if 'prosegui_step3' in request.POST:
            if not righe_data:
                # Non si può procedere senza almeno una riga
                messages.error(request, "Devi inserire almeno una riga per proseguire.")
                # Dobbiamo ricreare il form e il contesto anche in questo caso di errore
                form = DocumentoRigaForm()
            else:
                return redirect(reverse('documento_create_step3_scadenze'))
        else:
            # L'utente sta aggiungendo una nuova riga
            form = DocumentoRigaForm(request.POST)
            if form.is_valid():
                nuova_riga = form.cleaned_data
                
                # Calcoliamo i totali della riga
                imponibile_riga = nuova_riga['quantita'] * nuova_riga['prezzo_unitario']
                aliquota = AliquotaIVA.objects.get(pk=nuova_riga['aliquota_iva'].pk)
                iva_riga = imponibile_riga * (aliquota.valore_percentuale / Decimal(100))
                
                # Aggiungiamo i dati alla sessione
                righe_data.append({
                    'descrizione': nuova_riga['descrizione'],
                    'quantita': str(nuova_riga['quantita']),
                    'prezzo_unitario': str(nuova_riga['prezzo_unitario']),
                    'aliquota_iva_id': aliquota.pk,
                    'aliquota_iva_valore': str(aliquota.valore_percentuale),
                    'imponibile_riga': str(imponibile_riga.quantize(Decimal('0.01'))),
                    'iva_riga': str(iva_riga.quantize(Decimal('0.01'))),
                })
                
                request.session['doc_righe_data'] = righe_data
                # Reindirizziamo alla stessa pagina per "pulire" il form POST
                # e mostrare la nuova riga nella tabella. (Pattern Post-Redirect-Get)
                return redirect(reverse('documento_create_step2_righe'))
    else:
        form = DocumentoRigaForm()
        
    # Calcoliamo i totali attuali per il riepilogo
    totale_imponibile = sum(Decimal(r['imponibile_riga']) for r in righe_data)
    totale_iva = sum(Decimal(r['iva_riga']) for r in righe_data)
    
    context = {
        'form': form,
        'testata_data': testata_data,
        'righe_inserite': righe_data,
        'totale_imponibile': totale_imponibile,
        'totale_iva': totale_iva,
        'totale_documento': totale_imponibile + totale_iva
    }
    return render(request, 'gestionale/documento_create_step2.html', context)

@login_required
def documento_create_step3_scadenze(request):
    """
    Step 3 del wizard: inserimento scadenze e finalizzazione.
    """
    testata_data = request.session.get('doc_testata_data')
    righe_data = request.session.get('doc_righe_data')
    scadenze_data = request.session.get('doc_scadenze_data', [])

    if not testata_data or not righe_data:
        return redirect(reverse('documento_create_step1_testata'))
    
    # === NUOVA LOGICA DI ELIMINAZIONE SCADENZA (GESTITA CON GET) ===
    scadenza_da_eliminare_idx = request.GET.get('delete_scadenza')
    if scadenza_da_eliminare_idx is not None:
        try:
            scadenze_data.pop(int(scadenza_da_eliminare_idx))
            request.session['doc_scadenze_data'] = scadenze_data
            messages.success(request, "Scadenza eliminata con successo.")
        except (ValueError, IndexError):
            messages.error(request, "Errore durante l'eliminazione della scadenza.")
        return redirect(reverse('documento_create_step3_scadenze'))

    # Riconvertiamo le stringhe dalla sessione in Decimal prima di sommarle.
    totale_documento = sum(Decimal(r['imponibile_riga']) + Decimal(r['iva_riga']) for r in righe_data)
    totale_scadenze = sum(Decimal(s['importo_rata']) for s in scadenze_data)
    residuo_da_scadenzare = totale_documento - totale_scadenze

    if request.method == 'POST':
        # Creiamo un'istanza del form per aggiunta scadenza, che potrebbe servirci
        form = ScadenzaWizardForm(request.POST)

        if 'finalizza_documento' in request.POST:
            if residuo_da_scadenzare != 0:
                messages.error(request, "L'importo delle scadenze non corrisponde al totale del documento.")
                # Non facciamo return qui, lasciamo che la vista prosegua e mostri
                # la pagina con il messaggio di errore e il form vuoto pre-compilato.
                # Per farlo, dobbiamo ricreare il form con i valori di default.
                form = ScadenzaWizardForm(initial=get_scadenza_initial_data(testata_data, scadenze_data, residuo_da_scadenzare))

            else:
                # ... LA LOGICA DI SALVATAGGIO FINALE ... (la copio qui sotto per completezza)
                with transaction.atomic():
                    anagrafica = Anagrafica.objects.get(pk=testata_data['anagrafica_id'])
                    modalita_pagamento = ModalitaPagamento.objects.get(pk=testata_data['modalita_pagamento_id'])
                    cantiere = Cantiere.objects.get(pk=testata_data['cantiere_id']) if testata_data['cantiere_id'] else None

                    # === INIZIO LOGICA DI NUMERAZIONE AUTOMATICA ===
                    tipo_doc = testata_data['tipo_doc']
                    numero_doc_finale = "" # Inizializziamo la variabile

                    # Definiamo i prefissi per i documenti di vendita
                    prefissi_vendita = {
                        DocumentoTestata.TipoDoc.FATTURA_VENDITA: 'FT',
                        DocumentoTestata.TipoDoc.NOTA_CREDITO_VENDITA: 'NC',
                    }

                    if tipo_doc in prefissi_vendita:
                        prefisso = prefissi_vendita[tipo_doc]
                        anno_corrente = date.today().year
                        
                        # Troviamo l'ultimo documento dello stesso tipo e dello stesso anno
                        ultimo_documento = DocumentoTestata.objects.filter(
                            tipo_doc=tipo_doc,
                            data_documento__year=anno_corrente
                        ).order_by('numero_documento').last()

                        if ultimo_documento and ultimo_documento.numero_documento:
                            # Estraiamo il numero progressivo dall'ultimo numero documento
                            try:
                                ultimo_progressivo = int(ultimo_documento.numero_documento.split('-')[-1])
                                nuovo_progressivo = ultimo_progressivo + 1
                            except (IndexError, ValueError):
                                # Fallback se il formato non è quello atteso
                                nuovo_progressivo = 1
                        else:
                            nuovo_progressivo = 1
                        
                        # Componiamo il numero finale
                        numero_doc_finale = f"{prefisso}-{anno_corrente}-{nuovo_progressivo:06d}"
                    else:
                        numero_doc_finale = testata_data.get('numero_documento_manuale', 'ERRORE_NUM_MANCANTE')

                    # === FINE LOGICA DI NUMERAZIONE AUTOMATICA ===



                    nuova_testata = DocumentoTestata.objects.create(
                        tipo_doc=tipo_doc,
                        anagrafica=anagrafica,
                        data_documento=date.fromisoformat(testata_data['data_documento']),
                        numero_documento=numero_doc_finale, # <-- USIAMO IL NUMERO GENERATO
                        modalita_pagamento=modalita_pagamento,
                        cantiere=cantiere,
                        note=testata_data['note'],
                        imponibile=sum(Decimal(r['imponibile_riga']) for r in righe_data),
                        iva=sum(Decimal(r['iva_riga']) for r in righe_data),
                        totale=totale_documento,
                        stato=DocumentoTestata.Stato.CONFERMATO,
                        created_by=request.user,
                        updated_by=request.user
                    )
                    
                    for riga in righe_data:
                        DocumentoRiga.objects.create(
                            testata=nuova_testata, descrizione=riga['descrizione'], quantita=riga['quantita'],
                            prezzo_unitario=riga['prezzo_unitario'], aliquota_iva_id=riga['aliquota_iva_id'],
                            imponibile_riga=riga['imponibile_riga'], iva_riga=riga['iva_riga']
                        )
                    
                    for scadenza in scadenze_data:
                        Scadenza.objects.create(
                            documento=nuova_testata, anagrafica=anagrafica,
                            data_scadenza=date.fromisoformat(scadenza['data_scadenza']),
                            importo_rata=scadenza['importo_rata'],
                            tipo_scadenza=Scadenza.Tipo.INCASSO if 'V' in nuova_testata.tipo_doc else Scadenza.Tipo.PAGAMENTO
                        )
                    
                    clear_doc_wizard_session(request.session)
                    messages.success(request, f"Documento {nuova_testata} creato con successo!")
                    return redirect(nuova_testata.get_absolute_url())

        elif form.is_valid():
            nuova_scadenza = form.cleaned_data
            scadenze_data.append({
                'importo_rata': str(nuova_scadenza['importo_rata']),
                'data_scadenza': nuova_scadenza['data_scadenza'].isoformat(),
            })

            request.session['doc_scadenze_data'] = scadenze_data
            return redirect(reverse('documento_create_step3_scadenze'))
    else: # GET
        form = ScadenzaWizardForm(initial=get_scadenza_initial_data(testata_data, scadenze_data, residuo_da_scadenzare))

    context = {
        'form': form, 'totale_documento': totale_documento,
        'scadenze_inserite': scadenze_data, 'totale_scadenze': totale_scadenze,
        'residuo_da_scadenzare': residuo_da_scadenzare
    }
    return render(request, 'gestionale/documento_create_step3.html', context)

# === NUOVA FUNZIONE HELPER ===
# Per non ripetere il codice, ho estratto la logica di calcolo dei dati iniziali.
def get_scadenza_initial_data(testata_data, scadenze_data, residuo_da_scadenzare):
    data_proposta = None
    if scadenze_data:
        ultima_data = date.fromisoformat(scadenze_data[-1]['data_scadenza'])
        nuovo_mese, nuovo_anno = (ultima_data.month + 1, ultima_data.year)
        if nuovo_mese > 12:
            nuovo_mese, nuovo_anno = (1, nuovo_anno + 1)
        try:
            data_proposta = ultima_data.replace(year=nuovo_anno, month=nuovo_mese)
        except ValueError:
            data_proposta = ultima_data.replace(year=nuovo_anno, month=nuovo_mese, day=28)
    else:
        giorni_scadenza = 30
        try:
            mp_id = testata_data.get('modalita_pagamento_id')
            if mp_id:
                mp = ModalitaPagamento.objects.get(pk=mp_id)
                giorni_scadenza = mp.giorni_scadenza
        except ModalitaPagamento.DoesNotExist:
            pass
        data_documento = date.fromisoformat(testata_data['data_documento'])
        data_proposta = data_documento + timedelta(days=giorni_scadenza)

    return {
        'importo_rata': residuo_da_scadenzare,
        'data_scadenza': data_proposta.strftime('%Y-%m-%d')
    }


# ==============================================================================
# === VISTE API (per richieste AJAX)                                        ===
# ==============================================================================

@login_required
def get_anagrafiche_by_tipo(request):
    tipo_documento = request.GET.get('tipo_doc')
    anagrafiche_qs = Anagrafica.objects.none()

    # Logica per i documenti di VENDITA
    if tipo_documento in [DocumentoTestata.TipoDoc.FATTURA_VENDITA, DocumentoTestata.TipoDoc.NOTA_CREDITO_VENDITA]:
        anagrafiche_qs = Anagrafica.objects.filter(tipo=Anagrafica.Tipo.CLIENTE, attivo=True)
    
    # === NUOVA LOGICA PER I DOCUMENTI DI ACQUISTO ===
    elif tipo_documento in [DocumentoTestata.TipoDoc.FATTURA_ACQUISTO, DocumentoTestata.TipoDoc.NOTA_CREDITO_ACQUISTO]:
        anagrafiche_qs = Anagrafica.objects.filter(tipo=Anagrafica.Tipo.FORNITORE, attivo=True)

    data = [{'id': anag.pk, 'text': str(anag)} for anag in anagrafiche_qs]
    return JsonResponse({'results': data})

# ==============================================================================
# === VISTE DOCUMENTI (Dettaglio/Partitario)                              ===
# ==============================================================================

class DocumentoListView(TenantRequiredMixin, View): # Cambia da ListView a View
    """
    Mostra l'elenco paginato e filtrabile di tutti i documenti.
    """
    template_name = 'gestionale/documento_list.html'
    paginate_by = 15

    def get(self, request, *args, **kwargs):
        filter_form = DocumentoFilterForm(request.GET or None)
        
        # Queryset di base, ordinato come richiesto (ascendente)
        documenti_qs = DocumentoTestata.objects.select_related('anagrafica').order_by('data_documento', 'numero_documento')

        # Applica i filtri se il form è valido
        if filter_form.is_valid():
            
            tipo_doc = filter_form.cleaned_data.get('tipo_doc')
            if tipo_doc:
                documenti_qs = documenti_qs.filter(tipo_doc=tipo_doc)

            data_da = filter_form.cleaned_data.get('data_da')
            if data_da:
                documenti_qs = documenti_qs.filter(data_documento__gte=data_da)

            data_a = filter_form.cleaned_data.get('data_a')
            if data_a:
                documenti_qs = documenti_qs.filter(data_documento__lte=data_a)
        
        # Applica la paginazione al queryset già filtrato
        paginator = Paginator(documenti_qs, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'documenti': page_obj, # Passiamo l'oggetto pagina, non il queryset
            'is_paginated': page_obj.has_other_pages(),
            'page_obj': page_obj, # Passiamo l'oggetto pagina anche per il template di paginazione
            'filter_form': filter_form,
        }
        return render(request, self.template_name, context)

class DocumentoDetailView(TenantRequiredMixin, DetailView):
    model = DocumentoTestata
    template_name = 'gestionale/documento_detail.html'
    context_object_name = 'documento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documento = self.get_object()
        
        scadenze_con_pagato = Scadenza.objects.filter(documento=documento).annotate(
            pagato=Coalesce(
                Sum('pagamenti__importo'), 
                Value(0), 
                output_field=models.DecimalField()
            )).order_by('data_scadenza')
        
        
        totale_pagato_doc = 0
        for scadenza in scadenze_con_pagato:
            scadenza.residuo = scadenza.importo_rata - scadenza.pagato
            totale_pagato_doc += scadenza.pagato

        context['scadenze'] = scadenze_con_pagato
        context['totale_pagato'] = totale_pagato_doc
        context['saldo_residuo'] = documento.totale - totale_pagato_doc

        context['pagamento_form'] = PagamentoForm()
        
        return context
    
class DocumentoListExportExcelView(DocumentoListView):
    """
    Esporta la lista dei documenti in formato Excel.
    """
    def get(self, request, *args, **kwargs):
        documenti_qs = self.get_queryset()
        
        tenant_name = request.session.get('active_tenant_name', 'GestionaleDjango')
        report_title = 'Elenco Documenti'
        filename_prefix = 'Elenco_Documenti'
        
        headers = ["Tipo", "Numero", "Data", "Cliente/Fornitore", "Totale", "Stato"]
        data_rows = []
        for doc in documenti_qs:
            data_rows.append([
                doc.get_tipo_doc_display(),
                doc.numero_documento,
                doc.data_documento,
                doc.anagrafica.nome_cognome_ragione_sociale,
                doc.totale,
                doc.get_stato_display()
            ])
            
        return generate_excel_report(
            tenant_name, report_title, "Nessun filtro applicato", None, headers, data_rows,
            filename_prefix=filename_prefix
        )

class DocumentoListExportPdfView(DocumentoListView):
    """
    Esporta la lista dei documenti (non paginata) in formato PDF.
    """
    def get(self, request, *args, **kwargs):
        # get_queryset() riutilizza la logica della ListView base,
        # incluso l'ordinamento che avevamo definito.
        documenti_qs = self.get_queryset()
        
        context = {
            'tenant_name': request.session.get('active_tenant_name', 'GestionaleDjango'),
            'report_title': 'Elenco Documenti',
            'timestamp': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
            'documenti': documenti_qs,
        }
        
        return generate_pdf_report(
            request,
            'gestionale/documento_list_pdf.html', 
            context
        )

# ==============================================================================
# === VISTE PARTITARIO ANAGRAFICA (DETAIL + EXPORTS)                        ===
# ==============================================================================

class AnagraficaDetailView(TenantRequiredMixin, View):
    """
    Gestisce la visualizzazione del partitario e contiene la logica
    di recupero dati riutilizzata dagli export.
    """
    template_name = 'gestionale/anagrafica_detail.html'
    
    def _get_partitario_data(self, request, anagrafica_pk):
        """
        Metodo helper che recupera e filtra TUTTI i dati per il partitario.
        Questa è la fonte di verità per la vista HTML e per gli export.
        """
        anagrafica = get_object_or_404(Anagrafica, pk=anagrafica_pk)
        filter_form = PartitarioFilterForm(request.GET or None)
        
        # Queryset di base
        documenti_qs = DocumentoTestata.objects.filter(anagrafica=anagrafica, stato=DocumentoTestata.Stato.CONFERMATO)
        scadenze_qs = Scadenza.objects.filter(anagrafica=anagrafica, stato__in=[Scadenza.Stato.APERTA, Scadenza.Stato.PARZIALE])
        movimenti_qs = PrimaNota.objects.filter(anagrafica=anagrafica)

        # Applica filtri
        if filter_form.is_valid():
            data_da = filter_form.cleaned_data.get('data_da')
            if data_da:
                documenti_qs = documenti_qs.filter(data_documento__gte=data_da)
                scadenze_qs = scadenze_qs.filter(data_scadenza__gte=data_da)
                movimenti_qs = movimenti_qs.filter(data_registrazione__gte=data_da)
            data_a = filter_form.cleaned_data.get('data_a')
            if data_a:
                documenti_qs = documenti_qs.filter(data_documento__lte=data_a)
                scadenze_qs = scadenze_qs.filter(data_scadenza__lte=data_a)
                movimenti_qs = movimenti_qs.filter(data_registrazione__lte=data_a)
        
        # Applica ordinamenti e annotazioni
        documenti = documenti_qs.order_by('-data_documento')
        scadenze_aperte = scadenze_qs.annotate(
            pagato=Coalesce(Sum('pagamenti__importo'), Value(0), output_field=models.DecimalField())
        ).order_by('data_scadenza')
        movimenti = movimenti_qs.order_by('-data_registrazione')
        
        # Calcola KPI e residui
        for s in scadenze_aperte:
            s.residuo = s.importo_rata - s.pagato
        esposizione_documenti = sum(doc.totale if 'V' in doc.tipo_doc else -doc.totale for doc in documenti)
        netto_movimenti = sum(mov.importo if mov.tipo_movimento == PrimaNota.TipoMovimento.ENTRATA else -mov.importo for mov in movimenti)
        saldo_finale = esposizione_documenti - netto_movimenti
        
        return {
            "anagrafica": anagrafica, "filter_form": filter_form,
            "documenti": documenti, "scadenze_aperte": scadenze_aperte,
            "movimenti": movimenti, "esposizione_documenti": esposizione_documenti,
            "netto_movimenti": netto_movimenti, "saldo_finale": saldo_finale
        }

    def get(self, request, *args, **kwargs):
        """Metodo per la visualizzazione della pagina HTML."""
        partitario_data = self._get_partitario_data(request, kwargs['pk'])
        context = {}
        context.update(partitario_data)
        paginator_scadenze = Paginator(partitario_data['scadenze_aperte'], 5)
        page_number_scadenze = request.GET.get('pagina_scadenze', 1)
        context['scadenze_aperte'] = paginator_scadenze.get_page(page_number_scadenze)
        paginator_movimenti = Paginator(partitario_data['movimenti'], 10)
        page_number_movimenti = request.GET.get('pagina_movimenti', 1)
        context['movimenti'] = paginator_movimenti.get_page(page_number_movimenti)
        context['pagamento_form'] = PagamentoForm()
        return render(request, self.template_name, context)

class AnagraficaPartitarioExportExcelView(AnagraficaDetailView):
    """
    Esporta il partitario completo di un'anagrafica in formato Excel,
    utilizzando la utility centralizzata per report multi-sezione.
    """
    def get(self, request, *args, **kwargs):
        # 1. RECUPERO DATI
        # Chiamiamo il metodo helper della classe base (AnagraficaDetailView)
        # per ottenere tutti i dati del partitario, già filtrati.
        partitario_data = self._get_partitario_data(request, kwargs['pk'])
        anagrafica = partitario_data['anagrafica']

        # 2. PREPARAZIONE DEI DATI PER IL REPORT
        tenant_name = request.session.get('active_tenant_name', 'GestionaleDjango')
        report_title = f"Partitario {anagrafica.get_tipo_display()}: {anagrafica.nome_cognome_ragione_sociale}"
        
        # Prepariamo un nome di file pulito
        safe_anag_name = "".join(c for c in anagrafica.nome_cognome_ragione_sociale if c.isalnum() or c in " _-").rstrip()
        filename_prefix = f"Partitario_{safe_anag_name}"
        
        # Prepariamo la stringa dei filtri applicati
        filter_form = partitario_data['filter_form']
        filtri_attivi = []
        if filter_form.is_valid() and filter_form.cleaned_data:
             for name, value in filter_form.cleaned_data.items():
                if value:
                    label = filter_form.fields[name].label or name.title()
                    display_value = value.strftime('%d/%m/%Y') if isinstance(value, date) else str(value)
                    filtri_attivi.append(f"{label}: {display_value}")
        filtri_str = " | ".join(filtri_attivi) if filtri_attivi else "Nessun filtro"

        # Prepariamo il dizionario dei KPI
        kpi_report = {
            'Esposizione Documenti': partitario_data['esposizione_documenti'],
            'Netto Incassato/Pagato': partitario_data['netto_movimenti'],
            'Saldo Aperto Finale': partitario_data['saldo_finale']
        }

        # 3. COSTRUZIONE DELLE SEZIONI DEL REPORT
        # Creiamo una lista che conterrà i dizionari di ogni sezione.
        report_sections = []

        # Sezione 1: Storico Documenti
        doc_headers = ["Data", "Tipo", "Numero", "Totale"]
        doc_rows = []
        for doc in partitario_data['documenti']:
            doc_rows.append([
                doc.data_documento,
                doc.get_tipo_doc_display(),
                doc.numero_documento,
                doc.totale
            ])
        report_sections.append({
            'title': 'Storico Documenti (Confermati)', 
            'headers': doc_headers, 
            'rows': doc_rows
        })

        # Sezione 2: Scadenziario Aperto
        scad_headers = ["Data Scad.", "Rif. Doc.", "Tipo", "Importo Rata", "Residuo", "Stato Rata"]
        scad_rows = []
        for scadenza in partitario_data['scadenze_aperte']:
            scad_rows.append([
                scadenza.data_scadenza,
                scadenza.documento.numero_documento,
                scadenza.get_tipo_scadenza_display(),
                scadenza.importo_rata,
                scadenza.residuo,
                scadenza.get_stato_display()
            ])
        report_sections.append({
            'title': 'Scadenziario Aperto', 
            'headers': scad_headers, 
            'rows': scad_rows
        })

        # Sezione 3: Cronologia Movimenti
        mov_headers = ["Data", "Descrizione", "Importo", "Conto"]
        mov_rows = []
        for movimento in partitario_data['movimenti']:
            mov_rows.append([
                movimento.data_registrazione,
                movimento.descrizione,
                # Usiamo un importo con segno per indicare Entrata/Uscita
                movimento.importo * (1 if movimento.tipo_movimento == 'E' else -1),
                movimento.conto_finanziario.nome_conto
            ])
        report_sections.append({
            'title': 'Cronologia Movimenti', 
            'headers': mov_headers, 
            'rows': mov_rows
        })

        # 4. CHIAMATA ALLA FUNZIONE DI UTILITY
        # Passiamo tutti i dati preparati alla nostra funzione centralizzata.
        return generate_excel_report(
            tenant_name=tenant_name,
            report_title=report_title,
            filters_string=filtri_str,
            kpi_data=kpi_report,
            report_sections=report_sections, # La nuova lista di sezioni
            filename_prefix=filename_prefix
        )
    
class AnagraficaPartitarioExportPdfView(AnagraficaDetailView):
    def get(self, request, *args, **kwargs):
        partitario_data = self._get_partitario_data(request, kwargs['pk'])
        anagrafica = partitario_data['anagrafica']

        filter_form = partitario_data['filter_form']
        filtri_attivi = []
        if filter_form.is_valid() and filter_form.cleaned_data:
             for name, value in filter_form.cleaned_data.items():
                if value:
                    label = filter_form.fields[name].label or name.title()
                    display_value = value.strftime('%d/%m/%Y') if isinstance(value, date) else str(value)
                    filtri_attivi.append(f"{label}: {display_value}")
        filtri_str = " | ".join(filtri_attivi) if filtri_attivi else "Nessun filtro"
        
        context = {
            'tenant_name': request.session.get('active_tenant_name'),
            'report_title': f"Partitario {anagrafica.get_tipo_display()}",
            'timestamp': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
            'filtri_str': filtri_str,
            **partitario_data
        }
        
        return generate_pdf_report(
            request,
            'gestionale/partitario_pdf_template.html', 
            context
        )


class AnagraficaListExportExcelView(AnagraficaListView):
    """
    Esporta la lista delle anagrafiche (non paginata) in formato Excel.
    """
    def get(self, request, *args, **kwargs):
        # get_queryset() è un metodo di ListView che restituisce il queryset di base
        anagrafiche_qs = self.get_queryset()
        
        tenant_name = request.session.get('active_tenant_name', 'GestionaleDjango')
        report_title = 'Elenco Anagrafiche'
        filename_prefix = 'Elenco_Anagrafiche'
        
        headers = ["Codice", "Tipo", "Nome/Ragione Sociale", "P.IVA", "Codice Fiscale", "Città", "Stato"]
        data_rows = []
        for anag in anagrafiche_qs:
            data_rows.append([
                anag.codice,
                anag.get_tipo_display(),
                anag.nome_cognome_ragione_sociale,
                anag.p_iva,
                anag.codice_fiscale,
                anag.citta,
                "Attivo" if anag.attivo else "Non Attivo"
            ])
            
        return generate_excel_report(
            tenant_name, report_title, "Nessun filtro applicato", None, headers, data_rows,
            filename_prefix=filename_prefix
        )

class AnagraficaListExportPdfView(AnagraficaListView):
    """
    Esporta la lista delle anagrafiche (non paginata) in formato PDF.
    """
    def get(self, request, *args, **kwargs):
        anagrafiche_qs = self.get_queryset()
        
        context = {
            'tenant_name': request.session.get('active_tenant_name'),
            'report_title': 'Elenco Anagrafiche',
            'timestamp': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
            'anagrafiche': anagrafiche_qs,
        }
        
        return generate_pdf_report(
            request,
            'gestionale/anagrafica_list_pdf.html',
            context
        )
    
# ==============================================================================
# === VISTE PAGAMENTI                                                       ===
# ==============================================================================

class RegistraPagamentoView(TenantRequiredMixin, View):
    """
    Gestisce la registrazione di un pagamento/incasso per una scadenza.
    """
    def post(self, request, *args, **kwargs):
        form = PagamentoForm(request.POST)
        redirect_url = request.META.get('HTTP_REFERER', reverse('dashboard'))

        if form.is_valid():
            scadenza = get_object_or_404(Scadenza, pk=form.cleaned_data['scadenza_id'])
            importo_pagato = form.cleaned_data['importo_pagato']
            
            # --- PRIMA CORREZIONE QUI ---
            # Aggiungiamo output_field=models.DecimalField() a Coalesce
            query_pagato = Scadenza.objects.filter(pk=scadenza.pk).annotate(
                pagato=Coalesce(Sum('pagamenti__importo'), Value(0), output_field=models.DecimalField())
            ).first()
            pagato_precedente = query_pagato.pagato if query_pagato else Decimal('0.00')
            residuo_attuale = scadenza.importo_rata - pagato_precedente

            if importo_pagato > residuo_attuale:
                messages.error(request, f"L'importo inserito (€{importo_pagato}) supera il residuo (€{residuo_attuale:.2f}).")
                return redirect(redirect_url)

            with transaction.atomic():
                if scadenza.tipo_scadenza == Scadenza.Tipo.INCASSO:
                    causale, _ = Causale.objects.get_or_create(descrizione="INCASSO FATTURA CLIENTE")
                    tipo_movimento = PrimaNota.TipoMovimento.ENTRATA
                else:
                    causale, _ = Causale.objects.get_or_create(descrizione="PAGAMENTO FATTURA FORNITORE")
                    tipo_movimento = PrimaNota.TipoMovimento.USCITA
                
                PrimaNota.objects.create(
                    data_registrazione=form.cleaned_data['data_pagamento'],
                    descrizione=f"{causale.descrizione} - Doc. {scadenza.documento.numero_documento} - {scadenza.anagrafica.nome_cognome_ragione_sociale}",
                    importo=importo_pagato,
                    tipo_movimento=tipo_movimento,
                    conto_finanziario=form.cleaned_data['conto_finanziario'],
                    causale=causale,
                    anagrafica=scadenza.anagrafica,
                    scadenza_collegata=scadenza,
                    created_by=request.user
                )

                # --- SECONDA CORREZIONE QUI ---
                # Riutilizziamo la stessa logica robusta.
                # Il nuovo totale pagato è la somma di quanto già c'era più l'ultimo pagamento.
                nuovo_totale_pagato = pagato_precedente + importo_pagato
                
                if nuovo_totale_pagato >= scadenza.importo_rata:
                    scadenza.stato = Scadenza.Stato.SALDATA
                else:
                    scadenza.stato = Scadenza.Stato.PARZIALE
                scadenza.save()
            
            messages.success(request, "Pagamento registrato con successo.")
        else:
            # Rendiamo il messaggio di errore più specifico
            error_string = ". ".join([f"{key}: {value[0]}" for key, value in form.errors.items()])
            messages.error(request, f"Errore nella compilazione del form. {error_string}")
            
        return redirect(redirect_url)
    
# ==============================================================================
# === VISTE SCADENZIARIO                                                    ===
# ==============================================================================


class ScadenzarioListView(TenantRequiredMixin, View):
    """
    Gestisce la visualizzazione della dashboard dello Scadenziario.
    Questa classe contiene la logica principale per recuperare e filtrare i dati,
    che viene poi riutilizzata anche dalle viste di export.
    """
    template_name = 'gestionale/scadenzario_list.html'
    paginate_by = 15

    def _get_filtered_data(self, request):
        """
        Metodo helper ("privato") che centralizza tutta la logica di recupero dati.
        Viene chiamato sia dalla vista HTML che dalle viste di export.
        
        Restituisce:
        - scadenze_qs: Il queryset delle scadenze, già filtrato.
        - kpi: Un dizionario con i totali aggregati per i KPI.
        - filter_form: L'istanza del form dei filtri, popolata con i dati GET.
        - today: La data odierna.
        """
        from datetime import date
        today = date.today()

        # Inizializza il form con i parametri GET della richiesta (es. ?tipo=Incasso)
        filter_form = ScadenzarioFilterForm(request.GET or None)
        
        # Queryset di base: tutte le scadenze che non sono né 'Saldata' né 'Annullata'.
        # Usiamo select_related per ottimizzare le query, pre-caricando i dati
        # delle tabelle collegate Anagrafica e DocumentoTestata con un unico JOIN.
        scadenze_qs = Scadenza.objects.filter(
            stato__in=[Scadenza.Stato.APERTA, Scadenza.Stato.PARZIALE]
        ).select_related('anagrafica', 'documento').order_by('data_scadenza')

        # Applica i filtri al queryset se il form è stato inviato e i dati sono validi.
        if filter_form.is_valid():
            cleaned_data = filter_form.cleaned_data
            
            if cleaned_data.get('anagrafica'):
                scadenze_qs = scadenze_qs.filter(anagrafica=cleaned_data['anagrafica'])
            
            if cleaned_data.get('data_da'):
                scadenze_qs = scadenze_qs.filter(data_scadenza__gte=cleaned_data['data_da'])
            
            if cleaned_data.get('data_a'):
                scadenze_qs = scadenze_qs.filter(data_scadenza__lte=cleaned_data['data_a'])
            
            if cleaned_data.get('tipo'):
                scadenze_qs = scadenze_qs.filter(tipo_scadenza=cleaned_data['tipo'])
            
            if cleaned_data.get('stato') == 'scadute':
                scadenze_qs = scadenze_qs.filter(data_scadenza__lt=today)
            elif cleaned_data.get('stato') == 'a_scadere':
                scadenze_qs = scadenze_qs.filter(data_scadenza__gte=today)
        
        # Calcola i KPI aggregati sull'INTERO queryset GIA' FILTRATO.
        # Questa è una singola, efficiente query al database.
        kpi = scadenze_qs.aggregate(
            incassi_totali_rate=Coalesce(Sum('importo_rata', filter=models.Q(tipo_scadenza=Scadenza.Tipo.INCASSO)), Value(0), output_field=models.DecimalField()),
            pagamenti_totali_rate=Coalesce(Sum('importo_rata', filter=models.Q(tipo_scadenza=Scadenza.Tipo.PAGAMENTO)), Value(0), output_field=models.DecimalField()),
            incassi_pagati=Coalesce(Sum('pagamenti__importo', filter=models.Q(tipo_scadenza=Scadenza.Tipo.INCASSO)), Value(0), output_field=models.DecimalField()),
            pagamenti_pagati=Coalesce(Sum('pagamenti__importo', filter=models.Q(tipo_scadenza=Scadenza.Tipo.PAGAMENTO)), Value(0), output_field=models.DecimalField()),
            incassi_scaduti_rate=Coalesce(Sum('importo_rata', filter=models.Q(tipo_scadenza=Scadenza.Tipo.INCASSO, data_scadenza__lt=today)), Value(0), output_field=models.DecimalField()),
            pagamenti_scaduti_rate=Coalesce(Sum('importo_rata', filter=models.Q(tipo_scadenza=Scadenza.Tipo.PAGAMENTO, data_scadenza__lt=today)), Value(0), output_field=models.DecimalField()),
            incassi_scaduti_pagati=Coalesce(Sum('pagamenti__importo', filter=models.Q(tipo_scadenza=Scadenza.Tipo.INCASSO, data_scadenza__lt=today)), Value(0), output_field=models.DecimalField()),
            pagamenti_scaduti_pagati=Coalesce(Sum('pagamenti__importo', filter=models.Q(tipo_scadenza=Scadenza.Tipo.PAGAMENTO, data_scadenza__lt=today)), Value(0), output_field=models.DecimalField())
        )
        
        # Restituisce i dati pronti per essere usati.
        return scadenze_qs, kpi, filter_form, today

    def get(self, request, *args, **kwargs):
        """
        Metodo principale che gestisce la richiesta GET per la pagina HTML.
        Il suo compito è orchestrare la chiamata all'helper, gestire la paginazione
        e preparare il contesto finale per il template.
        """
        # 1. Chiama il metodo helper per ottenere tutti i dati di base.
        scadenze_qs, kpi_data, filter_form, today = self._get_filtered_data(request)

        # 2. Calcola i valori finali dei KPI dai dati aggregati.
        incassi_aperti = kpi_data['incassi_totali_rate'] - kpi_data['incassi_pagati']
        pagamenti_aperti = kpi_data['pagamenti_totali_rate'] - kpi_data['pagamenti_pagati']
        incassi_scaduti = kpi_data['incassi_scaduti_rate'] - kpi_data['incassi_scaduti_pagati']
        pagamenti_scaduti = kpi_data['pagamenti_scaduti_rate'] - kpi_data['pagamenti_scaduti_pagati']
        
        # 3. Applica la paginazione al queryset filtrato.
        paginator = Paginator(scadenze_qs, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # 4. Calcola il residuo per le sole scadenze della pagina corrente (per efficienza).
        ids_pagina_corrente = [s.id for s in page_obj]
        scadenze_pagina_con_pagato = Scadenza.objects.filter(pk__in=ids_pagina_corrente).annotate(
            pagato=Coalesce(Sum('pagamenti__importo'), Value(0), output_field=models.DecimalField())
        )
        pagato_map = {s.id: s.pagato for s in scadenze_pagina_con_pagato}

        for s in page_obj:
            s.residuo = s.importo_rata - pagato_map.get(s.id, Decimal(0))

        # 5. Prepara il contesto da passare al template.
        context = {
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'pagamento_form': PagamentoForm(), # Necessario per la modale
            'today': today,
            'filter_form': filter_form,
            'kpi': {
                'incassi_aperti': incassi_aperti,
                'pagamenti_aperti': pagamenti_aperti,
                'saldo_circolante': incassi_aperti - pagamenti_aperti,
                'incassi_scaduti': incassi_scaduti,
                'pagamenti_scaduti': pagamenti_scaduti,
            }
        }
        
        # 6. Renderizza il template con il contesto.
        return render(request, self.template_name, context)

class ScadenzarioExportExcelView(ScadenzarioListView):
    """
    Esporta i dati dello scadenziario in Excel, usando la utility centralizzata.
    """
    def get(self, request, *args, **kwargs):
        # 1. Recupera i dati filtrati e i KPI.
        scadenze_qs, kpi_data, filter_form, today = self._get_filtered_data(request)

        # 2. Prepara i dati per la funzione di utility.
        tenant_name = request.session.get('active_tenant_name', 'GestionaleDjango')
        report_title = 'Report Scadenziario Aperto'
        filename_prefix = 'Scadenziario_Aperto'
        
        # Costruisci la stringa dei filtri (logica che abbiamo già)
        filtri_attivi = []
        if filter_form.is_valid():
            for name, value in filter_form.cleaned_data.items():
                if value:
                    field = filter_form.fields.get(name)
                    if not field: continue
                    label = field.label or name.replace('_', ' ').title()
                    display_value = value
                    if hasattr(field, 'choices'):
                        display_value = dict(field.choices).get(value, value)
                    if isinstance(value, date):
                        display_value = value.strftime('%d/%m/%Y')
                    if isinstance(field, forms.ModelChoiceField):
                        display_value = str(value)
                    filtri_attivi.append(f"{label}: {display_value}")
        filtri_str = " | ".join(filtri_attivi) if filtri_attivi else "Tutti"
        
        # Prepara i KPI nel formato desiderato
        incassi_aperti = kpi_data['incassi_totali_rate'] - kpi_data['incassi_pagati']
        pagamenti_aperti = kpi_data['pagamenti_totali_rate'] - kpi_data['pagamenti_pagati']
        kpi_report = {
            'Incassi Aperti': incassi_aperti,
            'Pagamenti Aperti': pagamenti_aperti,
            'Saldo Circolante': incassi_aperti - pagamenti_aperti
        }

        # Definisci le intestazioni della tabella
        headers = [
            "Data Scad.", "Tipo", "Cliente/Fornitore", "Rif. Doc.", 
            "Importo Rata", "Residuo", "Stato Rata"
        ]
        
        # Prepara le righe di dati
        data_rows = []
        scadenze_con_pagato = scadenze_qs.annotate(
            pagato=Coalesce(Sum('pagamenti__importo'), Value(0), output_field=models.DecimalField())
        )
        for scadenza in scadenze_con_pagato:
            data_rows.append([
                scadenza.data_scadenza,
                scadenza.get_tipo_scadenza_display(),
                scadenza.anagrafica.nome_cognome_ragione_sociale,
                scadenza.documento.numero_documento,
                scadenza.importo_rata,
                scadenza.importo_rata - scadenza.pagato,
                scadenza.get_stato_display()
            ])
            
        # 3. Chiama la funzione di utility e restituisci il risultato.
        return generate_excel_report(
            tenant_name, report_title, filtri_str, kpi_report, headers, data_rows,
            filename_prefix=filename_prefix
        )

class ScadenzarioExportPdfView(ScadenzarioListView):
    """
    Esporta i dati dello scadenziario in PDF, usando la utility centralizzata.
    """
    def get(self, request, *args, **kwargs):
        # 1. Recupera i dati filtrati e i KPI.
        scadenze_qs, kpi_data, filter_form, today = self._get_filtered_data(request)

        # 2. Prepara i dati per il contesto del template PDF.
        # Calcola il residuo per ogni scadenza.
        scadenze_con_pagato = scadenze_qs.annotate(
            pagato=Coalesce(Sum('pagamenti__importo'), Value(0), output_field=models.DecimalField())
        )
        for scadenza in scadenze_con_pagato:
            scadenza.residuo = scadenza.importo_rata - scadenza.pagato
            
        # Costruisci la stringa dei filtri.
        filtri_attivi = []
        if filter_form.is_valid():
            for name, value in filter_form.cleaned_data.items():
                if value:
                    field = filter_form.fields.get(name)
                    if not field: continue
                    label = field.label or name.replace('_', ' ').title()
                    display_value = value
                    if hasattr(field, 'choices'):
                         display_value = dict(field.choices).get(value, value)
                    if isinstance(value, date):
                         display_value = value.strftime('%d/%m/%Y')
                    if isinstance(field, forms.ModelChoiceField):
                        display_value = str(value)
                    filtri_attivi.append(f"{label}: {display_value}")
        filtri_str = " | ".join(filtri_attivi) if filtri_attivi else "Tutti"

        # Calcola i valori finali dei KPI.
        incassi_aperti = kpi_data['incassi_totali_rate'] - kpi_data['incassi_pagati']
        pagamenti_aperti = kpi_data['pagamenti_totali_rate'] - kpi_data['pagamenti_pagati']
        incassi_scaduti = kpi_data['incassi_scaduti_rate'] - kpi_data['incassi_scaduti_pagati']
        pagamenti_scaduti = kpi_data['pagamenti_scaduti_rate'] - kpi_data['pagamenti_scaduti_pagati']

        # 3. Crea il dizionario di contesto.
        context = {
            'tenant_name': request.session.get('active_tenant_name', 'GestionaleDjango'),
            'report_title': 'Report Scadenziario Aperto',
            'timestamp': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
            'filtri_str': filtri_str,
            'scadenze': scadenze_con_pagato,
            'kpi': {
                'incassi_aperti': incassi_aperti,
                'pagamenti_aperti': pagamenti_aperti,
                'saldo_circolante': incassi_aperti - pagamenti_aperti,
                'incassi_scaduti': incassi_scaduti,
                'pagamenti_scaduti': pagamenti_scaduti,
            }
        }
        
        # 4. Chiama la funzione di utility e restituisci il risultato.
        return generate_pdf_report(
            request, 
            'gestionale/scadenzario_pdf_template.html', 
            context
        )


# ==============================================================================
# === VISTE HR (Human Resources)                                            ===
# ==============================================================================

class DashboardHRView(TenantRequiredMixin, View):
    """
    Mostra la dashboard per la pianificazione e consuntivazione giornaliera
    delle risorse umane.
    """
    template_name = 'gestionale/dashboard_hr.html'

    def get(self, request, *args, **kwargs):
        # 1. Determina la data di riferimento
        # Leggiamo l'anno, mese e giorno dall'URL. Se non ci sono, usiamo oggi.
        year = kwargs.get('year', today.year)
        month = kwargs.get('month', today.month)
        day = kwargs.get('day', today.day)
        try:
            data_riferimento = date(year, month, day)
        except ValueError:
            # Se la data nell'URL non è valida, usa oggi
            data_riferimento = date.today()
            
        # 2. Recupera tutti i dipendenti attivi
        dipendenti_attivi = Anagrafica.objects.filter(
            tipo=Anagrafica.Tipo.DIPENDENTE,
            attivo=True
        ).select_related('dettaglio_dipendente').order_by('nome_cognome_ragione_sociale')
        
        # 3. Recupera le attività del diario per la data di riferimento
        diario_del_giorno = DiarioAttivita.objects.filter(data=data_riferimento).select_related('cantiere_pianificato', 'mezzo_pianificato')
        
        # 4. Mappiamo le attività ai dipendenti per un accesso veloce
        mappa_diario = {d.dipendente_id: d for d in diario_del_giorno}
        
        # 5. Combiniamo i dati: per ogni dipendente, determiniamo il suo stato
        lista_dipendenti_con_stato = []
        for dip in dipendenti_attivi:
            attivita_giornaliera = mappa_diario.get(dip.pk)
            dip.attivita = attivita_giornaliera # Aggiungiamo l'attività all'oggetto dipendente
            lista_dipendenti_con_stato.append(dip)
            
        # TODO: Calcolare i KPI

        context = {
            'data_riferimento': data_riferimento,
            'giorno_precedente': data_riferimento - timedelta(days=1),
            'giorno_successivo': data_riferimento + timedelta(days=1),
            'dipendenti': lista_dipendenti_con_stato,
            # Passiamo anche i queryset per i futuri form di pianificazione
            'cantieri_disponibili': Cantiere.objects.filter(stato=Cantiere.Stato.APERTO),
            'mezzi_disponibili': MezzoAziendale.objects.filter(attivo=True),
            'attivita_form': DiarioAttivitaForm(),
        }
        
        return render(request, self.template_name, context)
    
class SalvaAttivitaDiarioView(TenantRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data_str = request.POST.get('data')
        dipendente_id = request.POST.get('dipendente_id')
        
        data = date.fromisoformat(data_str)
        redirect_url = reverse('dashboard_hr_data', kwargs={'year': data.year, 'month': data.month, 'day': data.day})
        
        attivita, created = DiarioAttivita.objects.get_or_create(
            data=data,
            dipendente_id=dipendente_id,
            defaults={'created_by': request.user}
        )
        
        form = DiarioAttivitaForm(request.POST, instance=attivita)

        if form.is_valid():
            istanza_salvata = form.save(commit=False)
            istanza_salvata.updated_by = request.user
            
            # === INIZIO CORREZIONE ===
            # Garantiamo che i campi numerici non siano mai None prima di salvare.
            # Se il form li restituisce come None, li impostiamo al loro valore di default (0).
            if istanza_salvata.ore_ordinarie is None:
                istanza_salvata.ore_ordinarie = 0
            if istanza_salvata.ore_straordinarie is None:
                istanza_salvata.ore_straordinarie = 0
            
            # Logica di business (ora più semplice)
            if istanza_salvata.ore_ordinarie > 0 or istanza_salvata.ore_straordinarie > 0:
                if not istanza_salvata.stato_presenza:
                    istanza_salvata.stato_presenza = DiarioAttivita.StatoPresenza.PRESENTE
            
            stati_assenza = [
                DiarioAttivita.StatoPresenza.ASSENTE_G,
                DiarioAttivita.StatoPresenza.ASSENTE_I
            ]
            if istanza_salvata.stato_presenza in stati_assenza:
                istanza_salvata.ore_ordinarie = 0
                istanza_salvata.ore_straordinarie = 0
            # === FINE CORREZIONE ===

            istanza_salvata.save()
            messages.success(request, f"Attività per {attivita.dipendente.nome_cognome_ragione_sociale} salvata con successo.")
        else:
            error_string = ". ".join([f"'{key}': {value[0]}" for key, value in form.errors.items()])
            messages.error(request, f"Errore nel salvataggio: {error_string}")
        
        return redirect(redirect_url)
    
# ==============================================================================
# === VISTE PRIMA NOTA                                                      ===
# ==============================================================================

# gestionale/views.py

class PrimaNotaListView(TenantRequiredMixin, View):
    """
    Gestisce la visualizzazione della dashboard di Prima Nota.
    Contiene la logica di recupero e filtraggio dati riutilizzabile dagli export.
    """
    template_name = 'gestionale/primanota_list.html'
    paginate_by = 15

    def _get_filtered_data(self, request):
        """
        Metodo helper che centralizza il recupero e il filtraggio dei movimenti.
        Restituisce il queryset filtrato e il form dei filtri.
        """
        filter_form = PrimaNotaFilterForm(request.GET or None)
        
        # Queryset di base con ottimizzazione select_related
        movimenti_qs = PrimaNota.objects.select_related(
            'conto_finanziario', 'causale', 'anagrafica', 'cantiere'
        ).order_by('-data_registrazione', '-pk')

        # Applica i filtri se il form è valido
        if filter_form.is_valid():
            cleaned_data = filter_form.cleaned_data
            if cleaned_data.get('descrizione'):
                movimenti_qs = movimenti_qs.filter(descrizione__icontains=cleaned_data['descrizione'])
            if cleaned_data.get('conto_finanziario'):
                movimenti_qs = movimenti_qs.filter(conto_finanziario=cleaned_data['conto_finanziario'])
            if cleaned_data.get('causale'):
                movimenti_qs = movimenti_qs.filter(causale=cleaned_data['causale'])
            if cleaned_data.get('data_da'):
                movimenti_qs = movimenti_qs.filter(data_registrazione__gte=cleaned_data['data_da'])
            if cleaned_data.get('data_a'):
                movimenti_qs = movimenti_qs.filter(data_registrazione__lte=cleaned_data['data_a'])
        
        return movimenti_qs, filter_form

    def get(self, request, *args, **kwargs):
        """
        Gestisce la richiesta GET per la pagina HTML.
        """
        movimenti_qs, filter_form = self._get_filtered_data(request)
        
        # Paginazione
        paginator = Paginator(movimenti_qs, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Contesto per il template
        context = {
            'movimenti': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'page_obj': page_obj,
            'filter_form': filter_form,
        }
        return render(request, self.template_name, context)

class PrimaNotaDeleteView(TenantRequiredMixin, DeleteView):
    """
    Gestisce l'eliminazione di un movimento di Prima Nota,
    mostrando un avviso speciale per i giroconti.
    """
    model = PrimaNota
    template_name = 'gestionale/primanota_confirm_delete.html'
    success_url = reverse_lazy('primanota_list')

    def form_valid(self, form):
        """
        Aggiunge un messaggio di successo dopo l'eliminazione.
        La logica di cancellazione del movimento collegato è nel modello.
        """
        messages.success(self.request, f"Movimento N. {self.object.pk} eliminato con successo.")
        return super().form_valid(form)


class PrimaNotaUpdateView(TenantRequiredMixin, UpdateView):
    """
    Gestisce la modifica di un movimento di Prima Nota.
    Contiene la logica speciale per sincronizzare i due movimenti
    quando si modifica un giroconto.
    """
    model = PrimaNota
    form_class = PrimaNotaUpdateForm # Usa il form specifico per la modifica (per la data)
    template_name = 'gestionale/primanota_form.html'
    
    def get_success_url(self):
        """
        Restituisce l'URL a cui reindirizzare dopo un salvataggio riuscito.
        """
        return reverse_lazy('primanota_list')

    def get_context_data(self, **kwargs):
        """
        Prepara il contesto per il template, popolando i campi extra se necessario.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = f"Modifica Movimento N. {self.object.pk}"
        
        # Passa l'ID della causale "Giroconto" per lo script JS.
        try:
            context['giroconto_causale_id'] = Causale.objects.get(descrizione__iexact="GIROCONTO").pk
        except Causale.DoesNotExist:
            context['giroconto_causale_id'] = None
            
        # Se stiamo modificando un giroconto, dobbiamo pre-popolare il campo
        # 'conto_destinazione' nel form, che non fa parte del modello.
        if self.object.movimento_collegato:
            form = context['form']
            # Il conto di "destinazione" è sempre il conto finanziario dell'altro movimento.
            form.initial['conto_destinazione'] = self.object.movimento_collegato.conto_finanziario

        return context
    
    def form_valid(self, form):
        """
        Questo metodo viene eseguito quando i dati inviati nel form sono validi.
        Contiene la logica di business per orchestrare il salvataggio.
        """
        # Recupera l'oggetto originale dal database, prima di qualsiasi modifica.
        movimento_originale = self.get_object()
        
        causale = form.cleaned_data.get('causale')
        is_giroconto = causale and causale.descrizione.upper() == 'GIROCONTO'

        # Eseguiamo sempre le modifiche in una transazione atomica per sicurezza.
        with transaction.atomic():
            # Ottieni l'oggetto aggiornato con i dati del form, ma non salvarlo ancora.
            movimento_aggiornato = form.save(commit=False)
            movimento_aggiornato.updated_by = self.request.user
            
            # --- CASO SPECIALE: GIROCONTO ---
            if is_giroconto:
                # Recupera il movimento collegato dal database.
                movimento_collegato = movimento_originale.movimento_collegato
                
                # Preserva il tipo_movimento del record principale, perché non arriva dal form.
                movimento_aggiornato.tipo_movimento = movimento_originale.tipo_movimento
                
                # Salva le modifiche al movimento principale.
                movimento_aggiornato.save()
                
                # Ora, se esiste un movimento collegato, sincronizzalo.
                if movimento_collegato:
                    # Recupera i conti dal form per aggiornare le descrizioni.
                    conto_origine = form.cleaned_data['conto_finanziario']
                    conto_destinazione = form.cleaned_data['conto_destinazione']

                    # Aggiorna i campi del movimento collegato con i nuovi valori.
                    movimento_collegato.data_registrazione = form.cleaned_data['data_registrazione']
                    movimento_collegato.importo = form.cleaned_data['importo']
                    movimento_collegato.updated_by = self.request.user

                    # Aggiorna la descrizione in modo speculare.
                    if movimento_collegato.tipo_movimento == PrimaNota.TipoMovimento.USCITA:
                        movimento_collegato.descrizione = f"GIROCONTO -> {conto_origine.nome_conto}"
                    else: # È un'entrata
                        movimento_collegato.descrizione = f"GIROCONTO <- {conto_destinazione.nome_conto}"
                    
                    movimento_collegato.save()
            
            # --- CASO NORMALE: MOVIMENTO STANDARD ---
            else:
                # Se non è un giroconto, salva semplicemente le modifiche.
                movimento_aggiornato.save()
        
        messages.success(self.request, f"Movimento N. {movimento_originale.pk} aggiornato con successo.")
        return HttpResponseRedirect(self.get_success_url())    

class PrimaNotaCreateView(TenantRequiredMixin, CreateView):
    """
    Gestisce la creazione di un nuovo movimento di Prima Nota.
    Contiene la logica speciale per creare due movimenti atomici
    quando la causale selezionata è "GIROCONTO".
    """
    model = PrimaNota
    form_class = PrimaNotaForm # Usa il form che gestisce dinamicamente i campi
    template_name = 'gestionale/primanota_form.html'
    
    def get_success_url(self):
        """
        Restituisce l'URL a cui reindirizzare dopo un salvataggio riuscito.
        """
        return reverse_lazy('primanota_list')

    def get_context_data(self, **kwargs):
        """
        Aggiunge dati extra al contesto del template.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuovo Movimento di Prima Nota'
        
        # Passiamo l'ID della causale "Giroconto" al template.
        # Questo ID verrà usato dallo script JavaScript per mostrare/nascondere
        # i campi del form in modo dinamico.
        try:
            context['giroconto_causale_id'] = Causale.objects.get(descrizione__iexact="GIROCONTO").pk
        except Causale.DoesNotExist:
            context['giroconto_causale_id'] = None
            
        return context

    def form_valid(self, form):
        """
        Questo metodo viene eseguito quando i dati inviati nel form sono validi.
        Contiene la logica di business per orchestrare il salvataggio.
        """
        causale = form.cleaned_data.get('causale')
        is_giroconto = causale and causale.descrizione.upper() == 'GIROCONTO'
        
        # --- CASO SPECIALE: GIROCONTO ---
        if is_giroconto:
            # Usiamo una transazione atomica per garantire l'integrità dei dati.
            # Se una delle operazioni di salvataggio fallisce, tutte le modifiche
            # al database vengono annullate.
            with transaction.atomic():
                conto_origine = form.cleaned_data['conto_finanziario']
                conto_destinazione = form.cleaned_data['conto_destinazione']
                importo = form.cleaned_data['importo']
                data_registrazione = form.cleaned_data['data_registrazione']
                
                # 1. Crea il movimento di USCITA
                # usiamo form.save(commit=False) per non salvare subito e poter
                # modificare i campi gestiti dal sistema.
                uscita = form.save(commit=False)
                uscita.created_by = self.request.user
                uscita.updated_by = self.request.user
                uscita.tipo_movimento = PrimaNota.TipoMovimento.USCITA
                uscita.descrizione = f"GIROCONTO -> {conto_destinazione.nome_conto}"
                uscita.save() # Primo salvataggio per ottenere un pk

                # 2. Crea il movimento di ENTRATA speculare
                entrata = PrimaNota.objects.create(
                    data_registrazione=data_registrazione,
                    descrizione=f"GIROCONTO <- {conto_origine.nome_conto}",
                    importo=importo,
                    tipo_movimento=PrimaNota.TipoMovimento.ENTRATA,
                    causale=causale,
                    conto_finanziario=conto_destinazione,
                    created_by=self.request.user,
                    movimento_collegato=uscita
                )
                
                # 3. Aggiorna il movimento di uscita per creare il legame bidirezionale
                uscita.movimento_collegato = entrata
                uscita.save()

            messages.success(self.request, "Giroconto registrato con successo.")

        # --- CASO NORMALE: MOVIMENTO STANDARD ---
        else:
            movimento = form.save(commit=False)
            movimento.created_by = self.request.user
            movimento.updated_by = self.request.user # Aggiungiamo anche updated_by per coerenza
            movimento.save()
            messages.success(self.request, "Movimento di prima nota creato con successo.")
            
        # Reindirizza alla pagina di successo in entrambi i casi.
        return HttpResponseRedirect(self.get_success_url())
    
class PrimaNotaListExportExcelView(PrimaNotaListView):
    """
    Esporta la lista filtrata dei movimenti di Prima Nota in formato Excel.
    Eredita da PrimaNotaListView per accedere al metodo _get_filtered_data.
    """
    def get(self, request, *args, **kwargs):
        # 1. RECUPERO DATI FILTRATI
        # Chiamiamo il nostro metodo helper per ottenere i dati esatti che l'utente vede.
        movimenti_qs, filter_form = self._get_filtered_data(request)
        
        # 2. PREPARAZIONE DEI DATI PER IL REPORT
        tenant_name = request.session.get('active_tenant_name', 'GestionaleDjango')
        report_title = 'Elenco Movimenti di Prima Nota'
        filename_prefix = 'Prima_Nota'
        
        # Costruisci la stringa dei filtri applicati
        filtri_attivi = []
        if filter_form.is_valid() and filter_form.cleaned_data:
            for name, value in filter_form.cleaned_data.items():
                if value:
                    label = filter_form.fields[name].label or name.title()
                    display_value = value
                    if hasattr(filter_form.fields[name], 'choices'):
                        display_value = dict(filter_form.fields[name].choices).get(value, value)
                    if isinstance(value, date):
                        display_value = value.strftime('%d/%m/%Y')
                    if isinstance(field, forms.ModelChoiceField): # 'field' non è definito, usiamo 'filter_form.fields[name]'
                        display_value = str(value)
                    filtri_attivi.append(f"{label}: {display_value}")
        filtri_str = " | ".join(filtri_attivi) if filtri_attivi else "Nessun filtro"

        # Definisci le sezioni del report (in questo caso solo una)
        headers = ["Data", "Descrizione", "Conto Finanziario", "Causale", "Entrata", "Uscita", "Anagrafica", "Cantiere"]
        data_rows = []
        for movimento in movimenti_qs:
            data_rows.append([
                movimento.data_registrazione,
                movimento.descrizione,
                movimento.conto_finanziario.nome_conto,
                movimento.causale.descrizione,
                movimento.importo if movimento.tipo_movimento == 'E' else None,
                movimento.importo if movimento.tipo_movimento == 'U' else None,
                str(movimento.anagrafica) if movimento.anagrafica else "",
                str(movimento.cantiere) if movimento.cantiere else "",
            ])
        
        report_sections = [{'title': 'Dettaglio Movimenti', 'headers': headers, 'rows': data_rows}]
        
        # 3. CHIAMATA ALLA FUNZIONE DI UTILITY
        # Deleghiamo tutta la complessità della creazione del file Excel.
        return generate_excel_report(
            tenant_name=tenant_name,
            report_title=report_title,
            filters_string=filtri_str,
            kpi_data=None, # Questo report non ha KPI
            report_sections=report_sections,
            filename_prefix=filename_prefix
        )
  
class PrimaNotaListExportPdfView(PrimaNotaListView):
    """
    Esporta la lista filtrata dei movimenti di Prima Nota in formato PDF.
    """
    def get(self, request, *args, **kwargs):
        # 1. Riutilizziamo la nostra logica centralizzata per ottenere i dati filtrati.
        movimenti_qs, filter_form = self._get_filtered_data(request)
        
        # 2. Prepariamo la stringa dei filtri applicati.
        filtri_attivi = []
        if filter_form.is_valid() and filter_form.cleaned_data:
            for name, value in filter_form.cleaned_data.items():
                if value:
                    label = filter_form.fields[name].label or name.title()
                    # Gestiamo i diversi tipi di campo per avere una visualizzazione pulita
                    if isinstance(value, date):
                        display_value = value.strftime('%d/%m/%Y')
                    elif isinstance(value, models.Model):
                        display_value = str(value)
                    else:
                        display_value = value
                    filtri_attivi.append(f"{label}: {display_value}")
        filtri_str = " | ".join(filtri_attivi) if filtri_attivi else "Nessun filtro"

        # 3. Prepariamo il contesto da passare al template PDF.
        context = {
            'tenant_name': request.session.get('active_tenant_name', 'GestionaleDjango'),
            'report_title': 'Elenco Movimenti di Prima Nota',
            'timestamp': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
            'filtri_str': filtri_str,
            'movimenti': movimenti_qs,
        }
        
        # 4. Chiamiamo la nostra utility per generare il PDF.
        return generate_pdf_report(
            request, 
            'gestionale/primanota_list_pdf.html', 
            context
        )
    
