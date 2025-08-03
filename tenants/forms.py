# tenants/forms.py

from django import forms

from accounts.models import User
from .models import Company
from .models import UserCompanyPermission

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['company_name', 'vat_number', 'is_active']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class UserPermissionForm(forms.ModelForm):
    class Meta:
        model = UserCompanyPermission
        fields = ['company', 'company_role']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'company_role': forms.Select(attrs={'class': 'form-select'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['company'].disabled = True

# FormSet per gestire una lista di UserPermissionForm
UserPermissionFormSet = forms.inlineformset_factory(
    User, # Il modello "genitore"
    UserCompanyPermission, # Il modello "figlio"
    form=UserPermissionForm, # Il form da usare per ogni riga
    extra=1, # Mostra sempre una riga vuota per aggiungere un nuovo permesso
    can_delete=True # Permette di cancellare i permessi esistenti
)

class AssociateUserForm(forms.Form):
    """
    Form per associare un utente esistente a un'azienda.
    """
    # Usiamo un ModelChoiceField per avere un menu a tendina con tutti gli utenti.
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Seleziona Utente",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # Usiamo un ChoiceField per i ruoli, prendendoli dal modello UserCompanyPermission.
    company_role = forms.ChoiceField(
        choices=UserCompanyPermission.CompanyRole.choices,
        label="Assegna Ruolo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        # Riceviamo l'azienda come argomento extra per poter escludere gli utenti già associati.
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            # Recupera gli ID degli utenti già associati a questa azienda tramite il modello-ponte
            utenti_gia_associati_ids = UserCompanyPermission.objects.filter(company=company).values_list('user__pk', flat=True)
            # Escludi questi utenti dal queryset del campo 'user'
            self.fields['user'].queryset = User.objects.exclude(pk__in=utenti_gia_associati_ids)

