# superadmin/views.py

from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.db import transaction
from tenants.models import Company # Importa il modello
from tenants.forms import CompanyForm # Importa il form
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import AdminPasswordChangeForm

# Importa i modelli e i form dalle altre app
from gestionale.views import SuperAdminRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import FormView
from accounts.models import User
from accounts.forms import CustomUserCreationForm, CustomUserChangeForm
from tenants.forms import UserPermissionFormSet

from django.utils import timezone
from datetime import timedelta

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
    
# === VISTE CRUD PER GLI UTENTI ===

class UserListView(SuperAdminRequiredMixin, ListView):
    model = User
    template_name = 'superadmin/user_list.html'
    context_object_name = 'utenti'
    ordering = ['username']

class UserCreateView(SuperAdminRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'superadmin/user_form.html'
    success_url = reverse_lazy('superadmin:user_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Utente creato con successo.")
        return super().form_valid(form)

class UserUpdateView(SuperAdminRequiredMixin, View):
    """
    Vista complessa per modificare un utente e i suoi permessi aziendali.
    """
    template_name = 'superadmin/user_form.html'

    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        user_form = CustomUserChangeForm(instance=user)
        permission_formset = UserPermissionFormSet(instance=user)
        
        context = {
            'user_form': user_form,
            'permission_formset': permission_formset,
            'object': user
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        user_form = CustomUserChangeForm(request.POST, instance=user)
        permission_formset = UserPermissionFormSet(request.POST, instance=user)

        if user_form.is_valid() and permission_formset.is_valid():
            with transaction.atomic():
                user_form.save()
                permission_formset.save()
            messages.success(request, "Utente e permessi aggiornati con successo.")
            return redirect('superadmin:user_list')
        else:
            context = {
                'user_form': user_form,
                'permission_formset': permission_formset,
                'object': user
            }
            return render(request, self.template_name, context)
        

 # === GESTIONE KPI ===
class SuperAdminDashboardView(SuperAdminRequiredMixin, View):
    template_name = 'superadmin/dashboard.html'

    def get(self, request, *args, **kwargs):
        # Calcolo KPI Aziende
        total_companies = Company.objects.count()
        active_companies = Company.objects.filter(is_active=True).count()
        
        # Calcolo KPI Utenti
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Calcolo Nuove Iscrizioni (aziende e utenti) negli ultimi 30 giorni
        trenta_giorni_fa = timezone.now() - timedelta(days=30)
        new_companies_last_month = Company.objects.filter(created_at__gte=trenta_giorni_fa).count()
        new_users_last_month = User.objects.filter(date_joined__gte=trenta_giorni_fa).count()

        context = {
            'kpi': {
                'total_companies': total_companies,
                'active_companies': active_companies,
                'total_users': total_users,
                'active_users': active_users,
                'new_companies_last_month': new_companies_last_month,
                'new_users_last_month': new_users_last_month,
            }
        }
        return render(request, self.template_name, context)
    

# === GESTIONE PASSWORD ===
class UserPasswordChangeView(SuperAdminRequiredMixin, PasswordChangeView):
    """
    Vista per permettere al Superadmin di cambiare la password di un altro utente.
    """
    # Usiamo il form dell'admin di Django che non richiede la vecchia password.
    form_class = AdminPasswordChangeForm
    template_name = 'superadmin/user_password_change_form.html'
    
    def get_success_url(self):
        """
        Reindirizza alla lista utenti dopo il cambio password.
        """
        messages.success(self.request, "Password aggiornata con successo.")
        return reverse_lazy('superadmin:user_list')

    def get_form_kwargs(self):
        """
        Passa l'oggetto 'user' al form.
        """
        kwargs = super().get_form_kwargs()
        # La vista PasswordChangeView si aspetta che l'utente da modificare
        # sia l'utente loggato. Noi lo "inganniamo" passandogli l'utente
        # che abbiamo recuperato dall'URL.
        kwargs['user'] = get_object_or_404(User, pk=self.kwargs['pk'])
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Aggiunge l'utente al contesto per mostrarne il nome nel template.
        """
        context = super().get_context_data(**kwargs)
        context['object'] = get_object_or_404(User, pk=self.kwargs['pk'])
        return context
    
