# gestionale/forms.py

from django import forms
from .models import Anagrafica, Cantiere, DipendenteDettaglio, DocumentoRiga, DocumentoTestata, AliquotaIVA,Scadenza, ContoFinanziario

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
            'tipo', 'nome_cognome_ragione_sociale', 
            'p_iva', 'codice_fiscale', 'indirizzo', 'cap', 'citta', 
            'provincia', 'email', 'telefono', 'attivo'
        ]

        # 3. (Opzionale ma utile) Permette di personalizzare i widget HTML
        #    per ogni campo. Qui stiamo dicendo a Django di usare
        #    classi CSS di Bootstrap per rendere i campi più belli.
        widgets = {            
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
        

    def clean_nome_cognome_ragione_sociale(self):
        # self.cleaned_data è un dizionario con i dati validati.
        data = self.cleaned_data['nome_cognome_ragione_sociale']
        return data.title() # Converte in Title Case (Es. "mario rossi" -> "Mario Rossi")

    def clean_p_iva(self):
        data = self.cleaned_data['p_iva']
        if data:
            # Rimuove tutto ciò che non è un numero
            return ''.join(filter(str.isdigit, data))
        return data

    def clean_codice_fiscale(self):
        data = self.cleaned_data['codice_fiscale']
        if data:
            return data.upper()
        return data

    def clean_indirizzo(self):
        data = self.cleaned_data['indirizzo']
        if data:
            return data.title()
        return data

    def clean_citta(self):
        data = self.cleaned_data['citta']
        if data:
            return data.title()
        return data

    def clean_provincia(self):
        data = self.cleaned_data['provincia']
        if data:
            return data.upper()
        return data

    def clean_email(self):
        data = self.cleaned_data['email']
        if data:
            return data.lower()
        return data

    def clean_telefono(self):
        data = self.cleaned_data['telefono']
        if data:
            return ''.join(filter(str.isdigit, data))
        return data
    
    def clean(self):
        """
        Validazione personalizzata per controllare l'unicità di P.IVA e Codice Fiscale.
        """
        # Esegui la validazione di base della classe genitore
        cleaned_data = super().clean()
        p_iva = cleaned_data.get("p_iva")
        codice_fiscale = cleaned_data.get("codice_fiscale")

        # self.instance è l'oggetto anagrafica che stiamo modificando.
        # In creazione, è un oggetto vuoto. In modifica, è l'oggetto esistente.
        
        # 1. Controlla la Partita IVA
        if p_iva:
            # Cerca anagrafiche con la stessa P.IVA, escludendo quella corrente.
            queryset = Anagrafica.objects.filter(p_iva=p_iva).exclude(pk=self.instance.pk)
            if queryset.exists():
                # Se trovi un duplicato, solleva un errore di validazione
                # che verrà mostrato all'utente vicino al campo 'p_iva'.
                self.add_error('p_iva', "Esiste già un'anagrafica con questa Partita IVA.")

        # 2. Controlla il Codice Fiscale
        if codice_fiscale:
            # Cerca anagrafiche con lo stesso C.F., escludendo quella corrente.
            queryset = Anagrafica.objects.filter(codice_fiscale=codice_fiscale).exclude(pk=self.instance.pk)
            if queryset.exists():
                self.add_error('codice_fiscale', "Esiste già un'anagrafica con questo Codice Fiscale.")
        
        return cleaned_data

class DipendenteDettaglioForm(forms.ModelForm):
    """
    Form per la creazione e modifica dei dettagli di un Dipendente.
    """
    class Meta:
        model = DipendenteDettaglio
        # Includiamo tutti i campi del modello tranne 'anagrafica',
        # perché la collegheremo noi automaticamente nella vista.
        fields = [
            'mansione', 'data_assunzione', 'data_fine_rapporto', 
            'ore_settimanali_contratto', 'giorni_lavorativi_settimana', 
            'costo_orario'
        ]

        widgets = {
            'mansione': forms.TextInput(attrs={'class': 'form-control'}),
            'data_assunzione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fine_rapporto': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ore_settimanali_contratto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'giorni_lavorativi_settimana': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'costo_orario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        
        # Rendiamo esplicito che data_fine_rapporto non è obbligatorio
        # sovrascrivendo le impostazioni di default del modello se necessario.
        # In questo caso, il modello ha già null=True, blank=True, quindi non è
        # strettamente necessario, ma è una buona pratica per chiarezza.
        required = {
            'data_fine_rapporto': False,
        }

    def clean_mansione(self):
        data = self.cleaned_data.get('mansione')
        if data:
            return data.upper()
        return data
    
class DocumentoTestataForm(forms.ModelForm):
    # === IL CAMPO DEVE ESSERE DEFINITO QUI, FUORI DALLA CLASSE META ===
    numero_documento_manuale = forms.CharField(
        label="Numero Documento (del fornitore)",
        required=False, # La validazione 'required' è gestita da JavaScript
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = DocumentoTestata
        fields = [
            'tipo_doc', 'anagrafica', 'data_documento', 
            'modalita_pagamento', 'cantiere', 'note'
        ]
        widgets = {
            'tipo_doc': forms.Select(attrs={'class': 'form-select'}),
            'anagrafica': forms.Select(attrs={'class': 'form-select'}),
            'data_documento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'modalita_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'cantiere': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cantiere'].queryset = Cantiere.objects.filter(attivo=True)
        self.fields['anagrafica'].queryset = Anagrafica.objects.none()

        if 'tipo_doc' in self.data:
            try:
                tipo_doc = self.data.get('tipo_doc')
                if tipo_doc in [DocumentoTestata.TipoDoc.FATTURA_VENDITA, DocumentoTestata.TipoDoc.NOTA_CREDITO_VENDITA]:
                    self.fields['anagrafica'].queryset = Anagrafica.objects.filter(tipo=Anagrafica.Tipo.CLIENTE, attivo=True)
                elif tipo_doc in [DocumentoTestata.TipoDoc.FATTURA_ACQUISTO, DocumentoTestata.TipoDoc.NOTA_CREDITO_ACQUISTO]:
                    self.fields['anagrafica'].queryset = Anagrafica.objects.filter(tipo=Anagrafica.Tipo.FORNITORE, attivo=True)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            if self.instance.tipo_doc in [DocumentoTestata.TipoDoc.FATTURA_VENDITA, DocumentoTestata.TipoDoc.NOTA_CREDITO_VENDITA]:
                self.fields['anagrafica'].queryset = Anagrafica.objects.filter(tipo=Anagrafica.Tipo.CLIENTE, attivo=True)
            elif self.instance.tipo_doc in [DocumentoTestata.TipoDoc.FATTURA_ACQUISTO, DocumentoTestata.TipoDoc.NOTA_CREDITO_ACQUISTO]:
                 self.fields['anagrafica'].queryset = Anagrafica.objects.filter(tipo=Anagrafica.Tipo.FORNITORE, attivo=True)
        # === LOGICA DI VALIDAZIONE ===
    def clean(self):
        """
        Validazione incrociata per l'unicità del documento fornitore.
        """
        cleaned_data = super().clean()
        
        tipo_doc = cleaned_data.get('tipo_doc')
        anagrafica = cleaned_data.get('anagrafica')
        numero_manuale = cleaned_data.get('numero_documento_manuale')

        # Eseguiamo questo controllo solo per i documenti di acquisto che hanno un numero
        tipi_passivi = [
            DocumentoTestata.TipoDoc.FATTURA_ACQUISTO, 
            DocumentoTestata.TipoDoc.NOTA_CREDITO_ACQUISTO
        ]
        
        if tipo_doc in tipi_passivi and anagrafica and numero_manuale:
            # Cerchiamo nel database se esiste già un documento con questa combinazione.
            # self.instance.pk ci assicura che in modifica non controlliamo l'oggetto stesso.
            if DocumentoTestata.objects.filter(
                anagrafica=anagrafica,
                tipo_doc=tipo_doc,
                numero_documento=numero_manuale
            ).exclude(pk=self.instance.pk).exists():
                
                # Se esiste, solleviamo un errore di validazione specifico
                # sul campo 'numero_documento_manuale'.
                self.add_error(
                    'numero_documento_manuale', 
                    f"Questo numero documento è già stato registrato per {anagrafica.nome_cognome_ragione_sociale}."
                )

        return cleaned_data
    

class DocumentoRigaForm(forms.ModelForm):
    class Meta:
        model = DocumentoRiga
        # Escludiamo i campi calcolati (imponibile, iva) e la testata,
        # perché li gestiremo noi nella vista.
        fields = ['descrizione', 'quantita', 'prezzo_unitario', 'aliquota_iva']
        widgets = {
            'descrizione': forms.TextInput(attrs={'class': 'form-control'}),
            'quantita': forms.NumberInput(attrs={'class': 'form-control'}),
            'prezzo_unitario': forms.NumberInput(attrs={'class': 'form-control'}),
            'aliquota_iva': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtriamo per mostrare solo le aliquote IVA attive.
        self.fields['aliquota_iva'].queryset = AliquotaIVA.objects.filter(attivo=True)

    def clean_descrizione(self):
        data = self.cleaned_data.get('descrizione')
        if data:
            return data.upper()
        return data

class ScadenzaWizardForm(forms.ModelForm):
    class Meta:
        model = Scadenza
        fields = ['importo_rata', 'data_scadenza']
        widgets = {
            'importo_rata': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_scadenza': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class PagamentoForm(forms.Form):
    """
    Form per registrare un pagamento/incasso di una scadenza.
    Non è un ModelForm perché crea un PrimaNota ma con logica custom.
    """
    # Usiamo un campo nascosto per passare l'ID della scadenza
    scadenza_id = forms.IntegerField(widget=forms.HiddenInput())
    
    data_pagamento = forms.DateField(
        label="Data Pagamento/Incasso",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )
    importo_pagato = forms.DecimalField(
        label="Importo Pagato/Incassato",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        required=True
    )
    conto_finanziario = forms.ModelChoiceField(
        label="Conto Finanziario (Cassa/Banca)",
        queryset=ContoFinanziario.objects.filter(attivo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    def clean_importo_pagato(self):
        # Validazione per assicurarsi che l'importo non sia negativo o zero
        importo = self.cleaned_data.get('importo_pagato')
        if importo <= 0:
            raise forms.ValidationError("L'importo deve essere maggiore di zero.")
        return importo
    
class ScadenzarioFilterForm(forms.Form):
    """
    Form per i filtri della dashboard scadenziario.
    """
    TIPO_CHOICES = (
        ('', 'Tutti i Tipi'),
        (Scadenza.Tipo.INCASSO, 'Incassi'),
        (Scadenza.Tipo.PAGAMENTO, 'Pagamenti'),
    )
    STATO_CHOICES = (
        ('aperte', 'Tutte Aperte'),
        ('scadute', 'Scadute'),
        ('a_scadere', 'A Scadere'),
    )

    anagrafica = forms.ModelChoiceField(
        queryset=Anagrafica.objects.filter(attivo=True).order_by('nome_cognome_ragione_sociale'),
        required=False,
        label="Filtra per Anagrafica",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    data_da = forms.DateField(
        required=False, 
        label="Data Scadenza Da",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_a = forms.DateField(
        required=False, 
        label="Data Scadenza A",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    stato = forms.ChoiceField(
        choices=STATO_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )