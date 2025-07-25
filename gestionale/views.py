# gestionale/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Anagrafica

        
# NOTA: Questa è una classe di supporto che useremo in TUTTE le viste del gestionale.
# La sua unica responsabilità è assicurarsi che un tenant sia attivo prima di
# eseguire qualsiasi altra logica.
class TenantRequiredMixin(LoginRequiredMixin, View):
    """
    Un Mixin che verifica che l'utente sia loggato e che un tenant
    sia attivo nella sessione.
    """
    def dispatch(self, request, *args, **kwargs):
        # Controlliamo se un tenant è attivo
        if not request.session.get('active_tenant_id'):
            return redirect(reverse('tenant_selection'))
        
        # Se tutto è ok, procedi con la normale esecuzione della vista
        return super().dispatch(request, *args, **kwargs)


# Abbiamo aggiornato la DashboardView per usare il nostro nuovo Mixin!
# È più pulito perché la logica di controllo del tenant è centralizzata.
class DashboardView(TenantRequiredMixin, View):
     def get(self, request, *args, **kwargs):
        # Ora non serve più controllare la sessione qui, lo fa il Mixin!
        active_tenant_name = request.session.get('active_tenant_name')
        user_company_role = request.session.get('user_company_role')
        
        context = {
            'active_tenant_name': active_tenant_name,
            'user_company_role': user_company_role,
        }
        
        return render(request, 'gestionale/dashboard.html', context)


# === NUOVA VISTA PER LA LISTA ANAGRAFICHE ===
class AnagraficaListView(TenantRequiredMixin, ListView):
    # 1. Quale modello deve usare questa lista?
    model = Anagrafica
    
    # 2. Quale template deve renderizzare?
    template_name = 'gestionale/anagrafica_list.html'
    
    # 3. Con quale nome deve passare la lista di oggetti al template?
    #    Se non lo specifichiamo, Django usa 'object_list' di default.
    #    'anagrafiche' è più esplicito e leggibile.
    context_object_name = 'anagrafiche'
    
    # 4. Quanti oggetti mostrare per pagina?
    #    Questo attiva automaticamente la paginazione.
    paginate_by = 15

    # NOTA: ListView fa tutto il lavoro di recuperare gli oggetti dal DB per noi!
    # Non dobbiamo scrivere Anagrafica.objects.all(), lo fa lei in background.

