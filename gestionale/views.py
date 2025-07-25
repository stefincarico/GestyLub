# gestionale/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Anagrafica
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .forms import AnagraficaForm 

        
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

# === NUOVA VISTA PER LA CREAZIONE DI ANAGRAFICHE ===
class AnagraficaCreateView(TenantRequiredMixin, CreateView):
    # 1. Quale modello stiamo creando?
    model = Anagrafica
    
    # 2. Quale form deve usare? Quello che abbiamo appena creato.
    form_class = AnagraficaForm
    
    # 3. Quale template deve renderizzare?
    #    CreateView e UpdateView possono usare lo stesso template,
    #    spesso chiamato _form.html per convenzione.
    template_name = 'gestionale/anagrafica_form.html'
    
    # 4. Dove reindirizzare l'utente dopo una creazione avvenuta con successo?
    #    Lo mandiamo indietro alla lista delle anagrafiche.
    success_url = reverse_lazy('anagrafica_list')

    def form_valid(self, form):
        """
        Questo metodo viene chiamato quando i dati del form sono validi.
        È il posto perfetto per aggiungere logica extra prima di salvare.
        """
        # Prima che il form venga salvato, impostiamo il campo 'created_by'
        # con l'utente attualmente loggato.
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        # Ora chiamiamo il metodo 'form_valid' della classe genitore (CreateView),
        # che si occuperà di salvare l'oggetto nel database.
        return super().form_valid(form)
    
