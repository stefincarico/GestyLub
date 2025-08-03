# tenants/forms.py

from django import forms
from django.core.exceptions import ValidationError

from accounts.models import User
from .models import Company
from .models import UserCompanyPermission

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['company_name', 'vat_number', 'is_active', 'address', 'email', 'phone', 'pec', 'iban', 'notes', 'cap', 'city', 'province']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DEMO SRL'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678901'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Es. email@domain.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. 3456789012'}),
            'pec': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'amministrazione@pec.demo.it'}),
            'iban': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. IT60X0542811101000000123456'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Qui le tue note...'}),
            'cap': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. 00100'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. ROMA'}),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EE per Estero'}),
        }

    def clean_vat_number(self):
        vat_number = self.cleaned_data.get('vat_number')
        if vat_number:
            if not vat_number.isdigit():
                raise ValidationError("La Partita IVA deve contenere solo numeri.", code='invalid_vat_format')
            if len(vat_number) < 11:
                raise ValidationError("La Partita IVA deve essere di almeno 11 cifre.", code='invalid_vat_length')
        return vat_number

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not phone.isdigit():
                raise ValidationError("Il numero di telefono deve contenere solo cifre.", code='invalid_phone_format')
        return phone

    def clean_cap(self):
        cap = self.cleaned_data.get('cap')
        if cap:
            if not cap.isdigit():
                raise ValidationError("Il CAP deve contenere solo numeri.", code='invalid_cap_format')
            if len(cap) != 5:
                raise ValidationError("Il CAP deve essere di 5 cifre.", code='invalid_cap_length')
        return cap

    def clean_province(self):
        province = self.cleaned_data.get('province')
        if province:
            if not province.isalpha():
                raise ValidationError("La Provincia deve contenere solo lettere.", code='invalid_province_format')
            if len(province) != 2:
                raise ValidationError("La Provincia deve essere di 2 lettere.", code='invalid_province_length')
        return province

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            # Applica l'UPPERCASE a tutti i campi di tipo stringa, tranne email e pec
            if isinstance(value, str) and field_name not in ['email', 'pec']:
                cleaned_data[field_name] = value.upper()
        return cleaned_data

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

