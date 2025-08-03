# superadmin/views.py
# Standard library imports
import os
import subprocess
from datetime import timedelta

# Django core imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, FormView, ListView, UpdateView

# Models imports
from accounts.models import User
from tenants.models import Company

# Forms imports
from accounts.forms import CustomUserCreationForm, CustomUserChangeForm
from tenants.forms import CompanyForm, UserPermissionFormSet

# Custom views/mixins
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
    
# === GESTIONE BACKUP ===
class DatabaseBackupView(SuperAdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Recupera le impostazioni del database da settings.py
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_pass = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']

        # Definisci il nome del file di backup con un timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{timestamp}_{db_name}_backup.sql"

        # Trova un percorso sicuro e comune dove salvare il backup, come la cartella 'Documenti' dell'utente
        # NOTA: Questo percorso dipende dall'utente che esegue il server Django
        user_docs = os.path.join(os.path.expanduser('~'), 'Documents')
        backup_filepath = os.path.join(user_docs, backup_filename)
        
        # Componi il comando pg_dump
        # Assicurati che il percorso di pg_dump.exe sia nella variabile d'ambiente PATH del sistema
        command = [
            "pg_dump",
            f"--host={db_host}",
            f"--port={db_port}",
            f"--username={db_user}",
            f"--dbname={db_name}",
            f"--file={backup_filepath}",
            "--format=p", # Formato plain-text SQL, facile da ispezionare
            "--no-password" # La password verrà passata tramite variabile d'ambiente
        ]

        # Imposta la password in una variabile d'ambiente solo per questo comando
        env = os.environ.copy()
        env['PGPASSWORD'] = db_pass

        try:
            # Esegui il comando
            subprocess.run(command, check=True, env=env, capture_output=True, text=True)
            messages.success(request, f"Backup del database '{db_name}' creato con successo in: {backup_filepath}")
        except FileNotFoundError:
            messages.error(request, "Errore: il comando 'pg_dump' non è stato trovato. Assicurarsi che la cartella 'bin' di PostgreSQL sia nella variabile d'ambiente PATH del sistema.")
        except subprocess.CalledProcessError as e:
            # Se pg_dump restituisce un errore, lo mostriamo all'utente
            messages.error(request, f"Errore durante l'esecuzione del backup: {e.stderr}")
        
        return redirect('superadmin:dashboard')
    
