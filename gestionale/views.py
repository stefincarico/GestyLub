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
    # 1. Non salviamo ancora l'oggetto nel database. commit=False
    #    ce lo restituisce in memoria.
    anagrafica = form.save(commit=False)
    
    # 2. Impostiamo l'utente che sta creando il record.
    anagrafica.created_by = self.request.user
    anagrafica.updated_by = self.request.user

    # --- LOGICA DI GENERAZIONE CODICE ---
    tipo = anagrafica.tipo
    prefisso = {
        Anagrafica.Tipo.CLIENTE: 'CL',
        Anagrafica.Tipo.FORNITORE: 'FO',
        Anagrafica.Tipo.DIPENDENTE: 'DI'
    }.get(tipo, 'XX') # 'XX' come default in caso di tipo non previsto

    # Cerchiamo l'ultimo record dello stesso tipo per trovare il numero più alto
    last_anagrafica = Anagrafica.objects.filter(tipo=tipo).order_by('codice').last()
    
    if last_anagrafica and last_anagrafica.codice:
        # Estraiamo il numero dal codice, lo convertiamo in intero, lo incrementiamo
        last_number = int(last_anagrafica.codice[2:])
        new_number = last_number + 1
    else:
        # Se non ci sono record, questo è il primo
        new_number = 1
        
    # Formattiamo il nuovo codice con 6 cifre, riempiendo con zeri (es. 000001)
    anagrafica.codice = f"{prefisso}{new_number:06d}"
    
    # 3. Ora che l'oggetto è completo, lo salviamo.
    anagrafica.save()

    # Il form ha bisogno che l'oggetto salvato sia assegnato a self.object
    # per funzionare correttamente con il reindirizzamento di success_url.
    self.object = anagrafica
    
    # Chiamiamo il metodo della classe base, ma dopo aver già salvato,
    # quindi non farà nulla di dannoso. In alternativa, e in modo più pulito,
    # potremmo semplicemente restituire il reindirizzamento.
    return super().form_valid(form)
    
