# superadmin/views.py

from django.shortcuts import render
from django.views import View
# Importiamo il mixin dall'app gestionale
from gestionale.views import SuperAdminRequiredMixin

class SuperAdminDashboardView(SuperAdminRequiredMixin, View):
    template_name = 'superadmin/dashboard.html'

    def get(self, request, *args, **kwargs):
        # TODO: Aggiungere qui i dati per la dashboard (conteggio utenti, aziende, etc.)
        context = {}
        return render(request, self.template_name, context)