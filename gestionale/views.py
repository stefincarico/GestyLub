# gestionale/views.py

# ==============================================================================
# === IMPORTAZIONI                                                          ===
# ==============================================================================
# Importazioni di Django
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect

# Importazioni delle app locali
from .models import Anagrafica, DipendenteDettaglio
from .forms import AnagraficaForm, DipendenteDettaglioForm


# ==============================================================================
# === MIXINS (Classi di supporto riutilizzabili)                            ===
# ==============================================================================

class TenantRequiredMixin(LoginRequiredMixin, View):
    """
    Un Mixin che verifica che l'utente sia loggato e che un tenant
    sia attivo nella sessione. Viene ereditato da tutte le viste del gestionale.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('active_tenant_id'):
            return redirect(reverse('tenant_selection'))
        return super().dispatch(request, *args, **kwargs)


# ==============================================================================
# === VISTE PRINCIPALI E ANAGRAFICHE                                        ===
# ==============================================================================

class DashboardView(TenantRequiredMixin, View):
    """
    Mostra la dashboard principale dell'applicazione.
    """
    def get(self, request, *args, **kwargs):
        active_tenant_name = request.session.get('active_tenant_name')
        user_company_role = request.session.get('user_company_role')
        
        context = {
            'active_tenant_name': active_tenant_name,
            'user_company_role': user_company_role,
        }
        
        return render(request, 'gestionale/dashboard.html', context)


class AnagraficaListView(TenantRequiredMixin, ListView):
    """
    Mostra l'elenco paginato di tutte le anagrafiche.
    """
    model = Anagrafica
    template_name = 'gestionale/anagrafica_list.html'
    context_object_name = 'anagrafiche'
    paginate_by = 15


class AnagraficaCreateView(TenantRequiredMixin, CreateView):
    """
    Gestisce la creazione di una nuova anagrafica (Step 1).
    Contiene la logica per la generazione automatica del codice
    e per il reindirizzamento condizionale.
    """
    model = Anagrafica
    form_class = AnagraficaForm
    template_name = 'gestionale/anagrafica_form.html'

    def get_success_url(self):
        """
        Decide dove reindirizzare l'utente dopo il salvataggio.
        """
        if self.object.tipo == Anagrafica.Tipo.DIPENDENTE:
            # Se è un dipendente, vai allo Step 2
            return reverse('dipendente_dettaglio_create', kwargs={'anagrafica_id': self.object.pk})
        else:
            # Altrimenti, vai alla lista
            return reverse('anagrafica_list')

    def form_valid(self, form):
        """
        Esegue la logica di salvataggio personalizzata.
        """
        with transaction.atomic():
            anagrafica = form.save(commit=False)
            
            anagrafica.created_by = self.request.user
            anagrafica.updated_by = self.request.user

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
            
            anagrafica.save()

        self.object = anagrafica
        return HttpResponseRedirect(self.get_success_url())


class DipendenteDettaglioCreateView(TenantRequiredMixin, CreateView):
    """
    Gestisce la creazione dei dettagli di un dipendente (Step 2).
    """
    model = DipendenteDettaglio
    form_class = DipendenteDettaglioForm
    template_name = 'gestionale/dipendente_dettaglio_form.html'
    success_url = reverse_lazy('anagrafica_list')

    def dispatch(self, request, *args, **kwargs):
        """
        Recupera l'anagrafica genitore prima di ogni altra cosa.
        """
        self.anagrafica = get_object_or_404(
            Anagrafica, 
            pk=self.kwargs['anagrafica_id'], 
            tipo=Anagrafica.Tipo.DIPENDENTE
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Passa l'anagrafica genitore al template per visualizzarne il nome.
        """
        context = super().get_context_data(**kwargs)
        context['anagrafica'] = self.anagrafica
        return context

    def form_valid(self, form):
        """
        Associa il dettaglio all'anagrafica genitore prima di salvare.
        """
        dettaglio = form.save(commit=False)
        dettaglio.anagrafica = self.anagrafica
        dettaglio.save()
        
        # === LA RIGA CHIAVE DA REINSERIRE ===
        # Dobbiamo impostare l'attributo 'object' della vista con l'oggetto
        # appena creato. Questo è necessario affinché il resto del
        # ciclo di vita della CreateView funzioni correttamente, incluso get_success_url().
        self.object = dettaglio
        
        return HttpResponseRedirect(self.get_success_url())

class AnagraficaUpdateView(TenantRequiredMixin, UpdateView):
    """
    Gestisce la modifica di un'anagrafica esistente.
    """
    model = Anagrafica
    form_class = AnagraficaForm
    template_name = 'gestionale/anagrafica_form.html' # Riutilizziamo lo stesso template!
    success_url = reverse_lazy('anagrafica_list')

    def form_valid(self, form):
        """
        Imposta l'utente che ha effettuato l'ultima modifica.
        """
        # Non serve la logica di generazione codice qui, perché il codice
        # non deve mai cambiare dopo la creazione.
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
class AnagraficaToggleAttivoView(TenantRequiredMixin, View):
    """
    Gestisce la disattivazione e riattivazione di un'anagrafica (soft delete).
    """
    def post(self, request, *args, **kwargs):
        # Usiamo POST per sicurezza, perché questa è un'azione che modifica i dati.
        anagrafica_id = kwargs.get('pk')
        anagrafica = get_object_or_404(Anagrafica, pk=anagrafica_id)
        
        # Invertiamo lo stato booleano 'attivo'.
        anagrafica.attivo = not anagrafica.attivo
        anagrafica.updated_by = request.user
        anagrafica.save()
        
        # Reindirizziamo l'utente alla lista anagrafiche.
        return redirect('anagrafica_list')
    
