# tenants/views.py

from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import UserCompanyPermission

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
        

