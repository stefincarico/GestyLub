# gestionale/views.py

# ==============================================================================
# === IMPORTAZIONI                                                          ===
# ==============================================================================
# Importazioni di Django
from django.db import models, transaction # <-- ASSICURATI CHE 'models' SIA QUI
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect

# Importazioni delle app locali
from .models import Anagrafica, DipendenteDettaglio, DocumentoTestata, Scadenza
from .forms import AnagraficaForm, DipendenteDettaglioForm


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
        with transaction.atomic():
            anagrafica = form.save(commit=False)
            anagrafica.created_by = self.request.user
            anagrafica.updated_by = self.request.user
            tipo = anagrafica.tipo
            prefisso = {'Cliente': 'CL', 'Fornitore': 'FO', 'Dipendente': 'DI'}.get(tipo, 'XX')
            last_anagrafica = Anagrafica.objects.filter(tipo=tipo).order_by('codice').last()
            if last_anagrafica and last_anagrafica.codice:
                last_number = int(last_anagrafica.codice[2:])
                new_number = last_number + 1
            else:
                new_number = 1
            anagrafica.codice = f"{prefisso}{new_number:06d}"
            anagrafica.save()
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