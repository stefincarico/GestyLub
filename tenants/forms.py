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

# FormSet per gestire una lista di UserPermissionForm
UserPermissionFormSet = forms.inlineformset_factory(
    User, # Il modello "genitore"
    UserCompanyPermission, # Il modello "figlio"
    form=UserPermissionForm, # Il form da usare per ogni riga
    extra=1, # Mostra sempre una riga vuota per aggiungere un nuovo permesso
    can_delete=True # Permette di cancellare i permessi esistenti
)

