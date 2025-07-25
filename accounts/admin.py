# accounts/admin.py

from pyexpat.errors import messages
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Creiamo una classe di amministrazione personalizzata per il nostro modello User.
# Ereditiamo da UserAdmin per avere tutte le funzionalità di default (gestione
# password, permessi, gruppi, etc.)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'system_role')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Ruoli Personalizzati', {'fields': ('system_role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Ruoli Personalizzati', {'fields': ('system_role',)}),
    )

    # === NUOVO METODO DI PROTEZIONE ===
    def save_model(self, request, obj, form, change):
        """
        Sovrascritto per impedire a un superuser di declassare se stesso
        se è l'ultimo superuser rimasto.
        """
        # 'obj' è l'utente che stiamo salvando.
        # 'request.user' è l'utente che sta compiendo l'azione.
        if obj == request.user: # Stiamo modificando noi stessi
            # Contiamo quanti superuser attivi ci sono
            active_superusers = User.objects.filter(is_superuser=True, is_active=True).count()
            
            # Se sto modificando me stesso E sono un superuser...
            if request.user.is_superuser:
                # ...e sto cercando di togliermi i privilegi di superuser O di disattivarmi...
                if (not form.cleaned_data.get('is_superuser') or 
                    not form.cleaned_data.get('is_active') or
                    form.cleaned_data.get('system_role') != User.SystemRole.SUPER_ADMIN):
                    
                    # ...e sono l'ultimo superuser rimasto...
                    if active_superusers <= 1:
                        # ...allora blocca l'azione e mostra un messaggio di errore.
                        messages.error(request, "Azione non consentita: non puoi rimuovere i privilegi all'ultimo Super Amministratore attivo.")
                        return # Interrompe il salvataggio
                        
        super().save_model(request, obj, form, change)

    # === NUOVO METODO DI PROTEZIONE (più semplice per la cancellazione) ===
    def get_queryset(self, request):
        """
        Sovrascritto per escludere l'utente corrente dalla lista di utenti
        che possono essere cancellati, se è l'unico superuser.
        """
        queryset = super().get_queryset(request)
        
        # Questa logica si applica solo nella pagina di cancellazione di massa (changelist)
        if 'delete' in request.POST.get('action', ''):
            active_superusers = User.objects.filter(is_superuser=True, is_active=True).count()
            if active_superusers <= 1 and request.user.is_superuser:
                 messages.error(request, "Azione non consentita: non puoi cancellare l'ultimo Super Amministratore.")
                 # Escludiamo l'utente corrente dal queryset da cancellare
                 return queryset.exclude(pk=request.user.pk)
                 
        return queryset

# Registriamo il nostro modello User con la nostra classe di amministrazione personalizzata.
admin.site.register(User, CustomUserAdmin)