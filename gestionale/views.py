# gestionale/views.py
# ==============================================================================
# === IMPORTAZIONI                                                          ===
# ==============================================================================
# Standard Library
import json
from datetime import date, timedelta, timezone
from decimal import Decimal

# Django Core
from django.db import models, transaction
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator

# Django Views
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView

# Django Auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone

from openpyxl import Workbook
import openpyxl
from openpyxl.styles import Font, Alignment

# Importazioni delle app locali
# Models
from .models import (
    AliquotaIVA,
    Anagrafica,
    Cantiere,
    DipendenteDettaglio,
    DocumentoRiga,
    DocumentoTestata,
    ModalitaPagamento,
    Scadenza,
    PrimaNota,
    Causale
)

# Forms
from .forms import (
    AnagraficaForm,
    DipendenteDettaglioForm,
    DocumentoRigaForm,
    DocumentoTestataForm,
    ScadenzaWizardForm,
    PagamentoForm,
    ScadenzarioFilterForm
)


# ==============================================================================
# === MIXINS                                                                ===
# ==============================================================================

class TenantRequiredMixin(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('active_tenant_id'):
            return redirect(reverse('tenant_selection'))
        return super().dispatch(request, *args, **kwargs)


# ==============================================================================
# === VISTE PRINCIPALI, ANAGRAFICHE E DOCUMENTI                             ===
# ==============================================================================

class DashboardView(TenantRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # ... (codice invariato) ...
        active_tenant_name = request.session.get('active_tenant_name')
        user_company_role = request.session.get('user_company_role')
        context = {'active_tenant_name': active_tenant_name, 'user_company_role': user_company_role}
        return render(request, 'gestionale/dashboard.html', context)

class AnagraficaListView(TenantRequiredMixin, ListView):
    # ... (codice invariato) ...
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

class DocumentoListView(TenantRequiredMixin, ListView):
    # ... (codice invariato) ...
    model = DocumentoTestata
    template_name = 'gestionale/documento_list.html'
    context_object_name = 'documenti'
    paginate_by = 15
    def get_queryset(self):
        return super().get_queryset().order_by('-data_documento', '-numero_documento')

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
                # === LA CORREZIONE È NELLA RIGA SEGUENTE ===
                # Usiamo models.DecimalField() che abbiamo importato correttamente
                output_field=models.DecimalField()
            )
        )
        
        totale_pagato_doc = 0
        for scadenza in scadenze_con_pagato:
            scadenza.residuo = scadenza.importo_rata - scadenza.pagato
            totale_pagato_doc += scadenza.pagato

        context['scadenze'] = scadenze_con_pagato
        context['totale_pagato'] = totale_pagato_doc
        context['saldo_residuo'] = documento.totale - totale_pagato_doc
        
        return context
    
# ==============================================================================
# === VISTE WIZARD CREAZIONE DOCUMENTO                                      ===
# ==============================================================================
def clear_doc_wizard_session(session):
    session.pop('doc_testata_data', None)
    session.pop('doc_righe_data', None)
    session.pop('doc_scadenze_data', None)


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
                    'quantita': float(nuova_riga['quantita']),
                    'prezzo_unitario': float(nuova_riga['prezzo_unitario']),
                    'aliquota_iva_id': aliquota.pk,
                    'aliquota_iva_valore': float(aliquota.valore_percentuale),
                    'imponibile_riga': str(imponibile_riga.quantize(Decimal('0.01'))),
                    'iva_riga': float(iva_riga),
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
                'importo_rata': float(nuova_scadenza['importo_rata']),
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
# === VISTE ANAGRAFICHE (Dettaglio/Partitario)                              ===
# ==============================================================================

class AnagraficaDetailView(TenantRequiredMixin, DetailView):
    """
    Mostra il partitario completo di un'anagrafica (Cliente o Fornitore).
    """
    model = Anagrafica
    template_name = 'gestionale/anagrafica_detail.html'
    context_object_name = 'anagrafica'

    def get_context_data(self, **kwargs):
        """
        Prepara tutti i dati aggregati per il partitario.
        """
        context = super().get_context_data(**kwargs)
        anagrafica = self.get_object()

        # 1. Recupera tutti i documenti confermati
        documenti = DocumentoTestata.objects.filter(
            anagrafica=anagrafica, 
            stato=DocumentoTestata.Stato.CONFERMATO
        ).order_by('-data_documento')

        # 2. Recupera lo scadenziario aperto
        scadenze_aperte = Scadenza.objects.filter(
            anagrafica=anagrafica,
            stato__in=[Scadenza.Stato.APERTA, Scadenza.Stato.PARZIALE]
        ).annotate(
            pagato=Coalesce(Sum('pagamenti__importo'), Value(0), output_field=models.DecimalField())
        ).order_by('data_scadenza')
        
        # Aggiungiamo il residuo calcolato a ogni scadenza
        for s in scadenze_aperte:
            s.residuo = s.importo_rata - s.pagato

        # 3. Recupera la cronologia di tutti i movimenti di Prima Nota
        movimenti = PrimaNota.objects.filter(anagrafica=anagrafica).order_by('-data_registrazione')

        # 4. Calcola i totali per il riepilogo contabile
        esposizione_documenti = sum(
            doc.totale if 'V' in doc.tipo_doc else -doc.totale 
            for doc in documenti
        )
        
        netto_movimenti = sum(
            mov.importo if mov.tipo_movimento == PrimaNota.TipoMovimento.ENTRATA else -mov.importo 
            for mov in movimenti
        )
        
        saldo_finale = esposizione_documenti - netto_movimenti

        # 5. Aggiungi tutto al contesto
        context['documenti'] = documenti
        context['scadenze_aperte'] = scadenze_aperte
        context['movimenti'] = movimenti
        context['esposizione_documenti'] = esposizione_documenti
        context['netto_movimenti'] = netto_movimenti
        context['saldo_finale'] = saldo_finale
        context['pagamento_form'] = PagamentoForm()

        return context
    
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
    Gestisce l'export in formato Excel (.xlsx) dello scadenziario.
    
    Eredita da ScadenzarioListView per poter riutilizzare il metodo
    _get_filtered_data, garantendo che i dati esportati siano
    esattamente quelli visualizzati e filtrati dall'utente.
    """
    
    def get(self, request, *args, **kwargs):
        # 1. RECUPERO DATI
        # Chiamiamo il nostro metodo helper centralizzato per ottenere
        # il queryset già filtrato e i dati aggregati per i KPI.
        scadenze_qs, kpi_data, filter_form, today = self._get_filtered_data(request)

        # 2. PREPARAZIONE DELLA RISPOSTA HTTP
        # Creiamo una risposta di tipo 'spreadsheet' (foglio di calcolo).
        # Il browser interpreterà questa risposta come un file da scaricare.
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        # Impostiamo l'header 'Content-Disposition' per suggerire al browser
        # il nome del file da scaricare.
        response['Content-Disposition'] = f'attachment; filename="scadenziario_aperto_{today.strftime("%Y%m%d")}.xlsx"'

        # 3. CREAZIONE DEL FILE EXCEL IN MEMORIA
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = 'Scadenziario Aperto'

        # 4. DEFINIZIONE DEGLI STILI (per un report più professionale)
        title_font = Font(name='Calibri', size=16, bold=True)
        header_font = Font(name='Calibri', size=12, bold=True)
        currency_format = '"€" #,##0.00'
        date_format = 'DD/MM/YYYY'

        # 5. SCRITTURA DELL'INTESTAZIONE DEL REPORT
        # Uniamo le celle per i titoli per un aspetto più pulito
        worksheet.merge_cells('A1:G1')
        worksheet.merge_cells('A2:G2')
        worksheet.merge_cells('A4:G4')
        worksheet.merge_cells('A5:G5')

        worksheet['A1'] = request.session.get('active_tenant_name', 'GestionaleDjango')
        worksheet['A1'].font = title_font
        worksheet['A1'].alignment = Alignment(horizontal='center')
        
        worksheet['A2'] = 'Report Scadenziario Aperto'
        worksheet['A2'].alignment = Alignment(horizontal='center')

        # Costruiamo la stringa dei filtri applicati
        filtri_attivi = []
        if filter_form.is_valid():
            for name, value in filter_form.cleaned_data.items():
                if value:
                    display_value = value
                    # Se il campo è un ChoiceField o ModelChoiceField, otteniamo l'etichetta leggibile
                    if hasattr(filter_form.fields[name], 'choices'):
                         display_value = dict(filter_form.fields[name].choices).get(value)
                    # Per le date, formattiamole
                    if isinstance(value, date):
                        display_value = value.strftime('%d/%m/%Y')
                    filtri_attivi.append(f"{filter_form.fields[name].label}: {display_value}")
        filtri_str = " | ".join(filtri_attivi) if filtri_attivi else "Nessun filtro"
        worksheet['A4'] = f"Filtri Applicati: {filtri_str}"
        
        worksheet['A5'] = f"Generato il: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}"
        
        # 6. SCRITTURA DEI KPI
        # Calcoliamo i valori finali dai dati aggregati
        incassi_aperti = kpi_data['incassi_totali_rate'] - kpi_data['incassi_pagati']
        pagamenti_aperti = kpi_data['pagamenti_totali_rate'] - kpi_data['pagamenti_pagati']
        saldo_circolante = incassi_aperti - pagamenti_aperti

        worksheet['B7'] = 'Incassi Aperti'; worksheet['C7'] = incassi_aperti
        worksheet['B8'] = 'Pagamenti Aperti'; worksheet['C8'] = pagamenti_aperti
        worksheet['B9'] = 'Saldo Circolante'; worksheet['C9'] = saldo_circolante
        
        for row in range(7, 10):
            worksheet[f'B{row}'].font = header_font
            worksheet[f'C{row}'].number_format = currency_format

        # 7. SCRITTURA DELLA TABELLA DATI
        # Intestazioni della tabella (a partire dalla riga 11 per lasciare spazio)
        headers = [
            "Data Scad.", "Tipo", "Cliente/Fornitore", "Rif. Doc.", 
            "Importo Rata", "Residuo", "Stato Rata"
        ]
        worksheet.append([]) # Aggiunge una riga vuota per spaziatura
        worksheet.append(headers)
        
        # Applica lo stile in grassetto all'ultima riga scritta (le intestazioni)
        for cell in worksheet[worksheet.max_row]:
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')

        # Eseguiamo l'annotate per calcolare il 'pagato' su tutto il queryset filtrato
        scadenze_con_pagato = scadenze_qs.annotate(
            pagato=Coalesce(Sum('pagamenti__importo'), Value(0), output_field=models.DecimalField())
        )
        
        # Scriviamo le righe di dati nel foglio
        for scadenza in scadenze_con_pagato:
            residuo = scadenza.importo_rata - scadenza.pagato
            row_data = [
                scadenza.data_scadenza,
                scadenza.get_tipo_scadenza_display(),
                scadenza.anagrafica.nome_cognome_ragione_sociale,
                scadenza.documento.numero_documento,
                scadenza.importo_rata,
                residuo,
                scadenza.get_stato_display()
            ]
            worksheet.append(row_data)
            
            # Applichiamo la formattazione specifica per data e valuta
            current_row = worksheet.max_row
            worksheet.cell(row=current_row, column=1).number_format = date_format
            worksheet.cell(row=current_row, column=5).number_format = currency_format
            worksheet.cell(row=current_row, column=6).number_format = currency_format
        
        # 8. ADATTAMENTO FINALE E SALVATAGGIO
        # Adatta automaticamente la larghezza delle colonne al contenuto
        
        # === INIZIO BLOCCO CORRETTO ===
        from openpyxl.utils import get_column_letter

        for col_idx in range(1, worksheet.max_column + 1):
            column_letter = get_column_letter(col_idx)
            max_length = 0
            # Cicliamo sulle celle della colonna
            for cell in worksheet[column_letter]:
                # Saltiamo le celle unite per evitare errori
                if isinstance(cell, openpyxl.cell.cell.MergedCell):
                    continue
                try:
                    # Troviamo la lunghezza massima del contenuto nella colonna
                    if len(str(cell.value or "")) > max_length:
                        max_length = len(str(cell.value or ""))
                except:
                    pass
            # Aggiungiamo un po' di padding alla larghezza
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        # === FINE BLOCCO CORRETTO ===

        # Salva il workbook nella risposta HTTP
        workbook.save(response)
        
        return response
    
