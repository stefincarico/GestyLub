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
        print("\n--- INIZIO PROCESSO DI BACKUP ---")
        
        try:
            db_settings = settings.DATABASES['default']
            db_name = db_settings.get('NAME')
            db_user = db_settings.get('USER')
            db_pass = db_settings.get('PASSWORD')
            db_host = db_settings.get('HOST')
            db_port = db_settings.get('PORT')
            print(f"1. Impostazioni DB caricate: DBNAME={db_name}, USER={db_user}")

            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{timestamp}_{db_name}_backup.sql"

            user_docs = os.path.join(os.path.expanduser('~'), 'Documents')
            if not os.path.exists(user_docs):
                print(f"AVVISO: La cartella Documenti '{user_docs}' non esiste. Tento di crearla.")
                os.makedirs(user_docs)
            
            backup_filepath = os.path.join(user_docs, backup_filename)
            print(f"2. Percorso del file di backup: {backup_filepath}")
            
            # Componiamo il comando pg_dump
            command = [
                "pg_dump",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
                f"--dbname={db_name}",
                f"--file={backup_filepath}",
                "--format=p",
                "--no-password",
            ]
            print(f"3. Comando da eseguire: {' '.join(command)}")

            env = os.environ.copy()
            env['PGPASSWORD'] = db_pass
            print("4. Password impostata in PGPASSWORD.")

            # Esegui il comando
            print("5. Esecuzione di subprocess.run...")
            # Aumentiamo il timeout per essere sicuri
            result = subprocess.run(
                command, env=env, check=True, 
                capture_output=True, text=True, timeout=60
            )
            
            print("6. Comando eseguito con successo.")
            print("   Output standard:", result.stdout)
            print("   Output errore:", result.stderr)
            messages.success(request, f"Backup creato con successo in: {backup_filepath}")

        except FileNotFoundError:
            print("ERRORE: FileNotFoundError. Il comando 'pg_dump' non è nel PATH.")
            messages.error(request, "Errore di configurazione: 'pg_dump' non trovato. Assicurarsi che la cartella 'bin' di PostgreSQL sia nella variabile d'ambiente PATH del sistema e riavviare il PC.")
        
        except subprocess.CalledProcessError as e:
            print(f"ERRORE: CalledProcessError. pg_dump ha restituito un errore.")
            print("   Return code:", e.returncode)
            print("   Output standard:", e.stdout)
            print("   Output errore (stderr):", e.stderr)
            messages.error(request, f"Errore durante l'esecuzione del backup: {e.stderr}")
        
        except subprocess.TimeoutExpired:
            print("ERRORE: TimeoutExpired. Il comando ha impiegato più di 60 secondi.")
            messages.error(request, "Errore: il processo di backup ha richiesto troppo tempo ed è stato interrotto.")
            
        except Exception as e:
            print(f"ERRORE GENERICO: {type(e).__name__} - {e}")
            messages.error(request, f"Si è verificato un errore imprevisto: {e}")
        
        finally:
            print("--- FINE PROCESSO DI BACKUP ---")

        return redirect('superadmin:dashboard')
    
