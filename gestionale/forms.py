# gestionale/forms.py

from django import forms
from .models import Anagrafica

class AnagraficaForm(forms.ModelForm):
    """
    Form per la creazione e modifica di un'Anagrafica.
    """
    class Meta:
        # 1. Dice al ModelForm da quale modello creare il form.
        model = Anagrafica
        
        # 2. Specifica quali campi del modello Anagrafica includere nel form.
        #    Escludiamo i campi che vengono gestiti automaticamente,
        #    come 'created_at', 'updated_at', 'created_by', ecc.
        fields = [
            'codice', 'tipo', 'nome_cognome_ragione_sociale', 
            'p_iva', 'codice_fiscale', 'indirizzo', 'cap', 'citta', 
            'provincia', 'email', 'telefono', 'attivo'
        ]

        # 3. (Opzionale ma utile) Permette di personalizzare i widget HTML
        #    per ogni campo. Qui stiamo dicendo a Django di usare
        #    classi CSS di Bootstrap per rendere i campi più belli.
        widgets = {
            'codice': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'nome_cognome_ragione_sociale': forms.TextInput(attrs={'class': 'form-control'}),
            'p_iva': forms.TextInput(attrs={'class': 'form-control'}),
            'codice_fiscale': forms.TextInput(attrs={'class': 'form-control'}),
            'indirizzo': forms.TextInput(attrs={'class': 'form-control'}),
            'cap': forms.TextInput(attrs={'class': 'form-control'}),
            'citta': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        # 4. (Opzionale) Personalizza le etichette dei campi se vuoi
        #    che siano diverse dal 'verbose_name' del modello.
        labels = {
            'nome_cognome_ragione_sociale': 'Nome/Cognome o Ragione Sociale',
            'p_iva': 'Partita IVA',
        }

