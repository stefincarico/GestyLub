# superadmin/views.py

from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from tenants.models import Company # Importa il modello
from tenants.forms import CompanyForm # Importa il form
# Importiamo il mixin dall'app gestionale
from gestionale.views import SuperAdminRequiredMixin

class SuperAdminDashboardView(SuperAdminRequiredMixin, View):
    template_name = 'superadmin/dashboard.html'

    def get(self, request, *args, **kwargs):
        # TODO: Aggiungere qui i dati per la dashboard (conteggio utenti, aziende, etc.)
        context = {}
        return render(request, self.template_name, context)
    
# === VISTE CRUD PER LE AZIENDE ===

class CompanyListView(SuperAdminRequiredMixin, ListView):
    model = Company
    template_name = 'superadmin/company_list.html'
    context_object_name = 'aziende'

class CompanyCreateView(SuperAdminRequiredMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'superadmin/company_form.html'
    success_url = reverse_lazy('superadmin:company_list')

    def form_valid(self, form):
        messages.success(self.request, "Azienda creata con successo. Il suo schema nel database è stato creato.")
        return super().form_valid(form)

class CompanyUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'superadmin/company_form.html'
    success_url = reverse_lazy('superadmin:company_list')

    def form_valid(self, form):
        messages.success(self.request, "Azienda aggiornata con successo.")
        return super().form_valid(form)
    
