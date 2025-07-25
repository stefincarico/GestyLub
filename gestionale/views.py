# gestionale/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
        # 1. Controlliamo se nella sessione dell'utente esiste la chiave 'active_tenant_id'.
        active_tenant_id = request.session.get('active_tenant_id')
        
        # 2. Se non c'è, significa che l'utente non ha selezionato un'azienda.
        #    Lo reindirizziamo alla pagina di selezione.
        if not active_tenant_id:
            return redirect(reverse('tenant_selection'))
        
        # 3. Se c'è, recuperiamo le altre informazioni che abbiamo salvato.
        active_tenant_name = request.session.get('active_tenant_name')
        user_company_role = request.session.get('user_company_role')
        
        # 4. Prepariamo il contesto da passare al template.
        context = {
            'active_tenant_name': active_tenant_name,
            'user_company_role': user_company_role,
        }
        
        return render(request, 'gestionale/dashboard.html', context)
        