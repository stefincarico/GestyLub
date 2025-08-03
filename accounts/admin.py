# accounts/admin.py

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from .models import User

# Definiamo la nostra classe di amministrazione personalizzata per il modello User
@admin.register(User) # Questo "decoratore" è un modo più moderno e pulito per registrare un modello.
class CustomUserAdmin(UserAdmin):
    """
    Configurazione personalizzata per il modello User nel pannello di amministrazione.
    """
    # Campi da visualizzare nella lista degli utenti
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'system_role', 'is_active')
    
    # Filtri che appaiono nella barra laterale destra
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'system_role')

    # I 'fieldsets' definiscono la struttura del form di modifica/creazione
    # Copiamo i fieldset di default e aggiungiamo la nostra sezione.
    fieldsets = UserAdmin.fieldsets + (
        ('Ruoli Personalizzati', {'fields': ('system_role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Ruoli Personalizzati', {'fields': ('system_role',)}),
    )

    def save_model(self, request, obj, form, change):
        """
        Impedisce a un superuser di declassare se stesso se è l'ultimo rimasto.
        """
        if obj == request.user and request.user.is_superuser:
            active_superusers = User.objects.filter(is_superuser=True, is_active=True).count()
            
            is_demoting_self = (
                not form.cleaned_data.get('is_superuser') or 
                not form.cleaned_data.get('is_active') or
                form.cleaned_data.get('system_role') != User.SystemRole.SUPER_ADMIN
            )

            if is_demoting_self and active_superusers <= 1:
                messages.error(request, "Azione non consentita: non puoi rimuovere i privilegi all'ultimo Super Amministratore attivo.")
                return 
                        
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """
        Impedisce la cancellazione di massa dell'ultimo superuser.
        """
        queryset = super().get_queryset(request)
        
        if 'delete' in request.POST.get('action', ''):
            active_superusers = User.objects.filter(is_superuser=True, is_active=True).count()
            
            # Se l'utente corrente è tra quelli selezionati per la cancellazione
            if str(request.user.pk) in request.POST.getlist('_selected_action'):
                if active_superusers <= 1 and request.user.is_superuser:
                    messages.error(request, "Azione non consentita: non puoi cancellare l'ultimo Super Amministratore.")
                    return queryset.exclude(pk=request.user.pk).order_by('username', 'pk')
                 
        return queryset.order_by('username', 'pk')