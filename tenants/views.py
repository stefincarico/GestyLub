# tenants/views.py

from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import UserCompanyPermission
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse


# LoginRequiredMixin è un "superpotere" di Django. Messo prima di View,
# controlla automaticamente se l'utente è loggato. Se non lo è, lo
# reindirizza alla pagina di login definita in settings.py.
class TenantSelectionView(LoginRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
        # Questa è la logica che viene eseguita quando la pagina viene caricata.
        
        # 1. Recuperiamo l'utente attualmente loggato.
        user = request.user
        
        # 2. Usiamo l'ORM di Django per interrogare il database.
        #    Filtriamo la tabella UserCompanyPermission per trovare tutti i permessi
        #    associati al nostro utente.
        #    'select_related("company")' è un'ottimizzazione: dice a Django di
        #    recuperare anche i dati dell'azienda collegata con una sola query,
        #    evitando query multiple e rendendo il tutto più veloce.
        permissions = UserCompanyPermission.objects.filter(user=user).select_related('company')
        
        # 3. Estraiamo solo le aziende dalla lista dei permessi.
        companies = [p.company for p in permissions if p.company.is_active]
        
        # 4. TODO (Lavoro Futuro): Se l'utente ha accesso a una sola azienda,
        #    potremmo reindirizzarlo direttamente alla dashboard di quella azienda.
        #    Per ora, mostriamo la pagina di selezione in ogni caso.
        
        # 5. Passiamo la lista di aziende al template.
        context = {
            'companies': companies
        }
        
        return render(request, 'tenants/tenant_selection.html', context)
        
class ActivateTenantView(LoginRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
        # 1. Recuperiamo l'ID dell'azienda dall'URL.
        #    'company_id' è un parametro che definiremo nel file urls.py.
        company_id = kwargs.get('company_id')
        
        # 2. Verifichiamo che l'utente abbia il permesso per questa azienda.
        #    get_object_or_404 è una scorciatoia utilissima: prova a trovare l'oggetto.
        #    Se non lo trova, mostra automaticamente una pagina di errore 404 (Not Found).
        #    Questo impedisce a un utente di provare ad attivare un'azienda a cui non
        #    ha accesso semplicemente indovinandone l'ID nell'URL.
        permission = get_object_or_404(
            UserCompanyPermission, 
            user=request.user, 
            company_id=company_id, 
            company__is_active=True # Assicuriamoci che l'azienda sia attiva
        )
        
        # 3. Se il permesso esiste, salviamo le informazioni nella sessione.
        #    La sessione di Django si comporta come un dizionario.
        request.session['active_tenant_id'] = permission.company.id
        request.session['active_tenant_name'] = permission.company.company_name
        request.session['user_company_role'] = permission.company_role
        
        # 4. Reindirizziamo l'utente alla dashboard principale.
        #    'reverse' è come 'reverse_lazy', ma si usa dentro le viste.
        #    Trova l'URL che ha come nome 'dashboard'. Lo creeremo tra poco.
        return redirect(reverse('dashboard'))
    

