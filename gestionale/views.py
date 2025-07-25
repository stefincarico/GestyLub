# gestionale/views.py

# Importazioni di Django
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.db import transaction

# Importazioni delle app locali
from .models import Anagrafica
from .forms import AnagraficaForm 


# ==============================================================================
# === MIXINS (Classi di supporto riutilizzabili)                            ===
# ==============================================================================

class TenantRequiredMixin(LoginRequiredMixin, View):
    """
    Un Mixin che verifica che l'utente sia loggato e che un tenant
    sia attivo nella sessione.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('active_tenant_id'):
            return redirect(reverse('tenant_selection'))
        return super().dispatch(request, *args, **kwargs)


# ==============================================================================
# === VISTE PRINCIPALI                                                      ===
# ==============================================================================

class DashboardView(TenantRequiredMixin, View):
     def get(self, request, *args, **kwargs):
        active_tenant_name = request.session.get('active_tenant_name')
        user_company_role = request.session.get('user_company_role')
        
        context = {
            'active_tenant_name': active_tenant_name,
            'user_company_role': user_company_role,
        }
        
        return render(request, 'gestionale/dashboard.html', context)


class AnagraficaListView(TenantRequiredMixin, ListView):
    model = Anagrafica
    template_name = 'gestionale/anagrafica_list.html'
    context_object_name = 'anagrafiche'
    paginate_by = 15


class AnagraficaCreateView(TenantRequiredMixin, CreateView):
    model = Anagrafica
    form_class = AnagraficaForm
    template_name = 'gestionale/anagrafica_form.html'
    success_url = reverse_lazy('anagrafica_list')

    # QUESTO METODO APPARTIENE ALLA CLASSE AnagraficaCreateView
    # NOTA L'INDENTAZIONE
    def form_valid(self, form):
        """
        Questo metodo viene chiamato quando i dati del form sono validi.
        Sovrascriviamo il comportamento di default per aggiungere la nostra logica.
        """
        # transaction.atomic assicura che tutte le query seguenti
        # vengano eseguite come un'unica operazione.
        with transaction.atomic():
            # 1. Otteniamo l'oggetto dal form senza salvarlo ancora nel DB.
            anagrafica = form.save(commit=False)
            
            # 2. Impostiamo i campi gestiti dal sistema.
            anagrafica.created_by = self.request.user
            anagrafica.updated_by = self.request.user

            # --- Inizio Logica di Generazione Codice ---
            tipo = anagrafica.tipo
            prefisso = {
                Anagrafica.Tipo.CLIENTE: 'CL',
                Anagrafica.Tipo.FORNITORE: 'FO',
                Anagrafica.Tipo.DIPENDENTE: 'DI'
            }.get(tipo, 'XX')

            last_anagrafica = Anagrafica.objects.filter(tipo=tipo).order_by('codice').last()
            
            if last_anagrafica and last_anagrafica.codice:
                last_number = int(last_anagrafica.codice[2:])
                new_number = last_number + 1
            else:
                new_number = 1
                
            anagrafica.codice = f"{prefisso}{new_number:06d}"
            # --- Fine Logica di Generazione Codice ---
            
            # 3. Ora che l'oggetto è completo, lo salviamo.
            anagrafica.save()

        # 4. Assegniamo l'oggetto finale alla vista.
        self.object = anagrafica
        
        # 5. Eseguiamo il reindirizzamento.
        return HttpResponseRedirect(self.get_success_url())