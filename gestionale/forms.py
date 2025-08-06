# gestionale/forms.py

from django import forms
from django.db import models
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from .models import (Anagrafica, Cantiere, Causale, ContoOperativo, 
        DipendenteDettaglio, DocumentoRiga, DocumentoTestata, AliquotaIVA, ModalitaPagamento, PrimaNota,
        Scadenza, ContoFinanziario, DiarioAttivita, MezzoAziendale, ScadenzaPersonale, TipoScadenzaPersonale)

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

class AnagraficaFilterForm(forms.Form):
    """
    Form per i filtri della lista anagrafiche.
    """
    TIPO_CHOICES = (('', 'Tutti i Tipi'),) + tuple(Anagrafica.Tipo.choices)
    STATO_CHOICES = (
        ('', 'Tutti gli Stati'),
        ('true', 'Attivo'),
        ('false', 'Non Attivo'),
    )

    q = forms.CharField(
        required=False,
        label="Cerca",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome, P.IVA, Città...'})
    )
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        label="Tipo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    attivo = forms.ChoiceField(
        choices=STATO_CHOICES,
        required=False,
        label="Stato",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class DipendenteDettaglioForm(forms.ModelForm):
    """
    Form per la creazione e modifica dei dettagli di un Dipendente.
    """
    class Meta:
        model = DipendenteDettaglio
        fields = [
            'mansione', 'data_assunzione', 'data_fine_rapporto', 
            'ore_settimanali_contratto', 'giorni_lavorativi_settimana',
            'costo_orario', 'note_generali'
        ]
        widgets = {
            'mansione': forms.TextInput(attrs={'class': 'form-control'}),
            'data_assunzione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fine_rapporto': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ore_settimanali_contratto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'giorni_lavorativi_settimana': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'costo_orario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note_generali': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inizializzazione personalizzata per formattare le date
        per i widget HTML di tipo 'date'.
        """
        super().__init__(*args, **kwargs)
        # Se il form è legato a un'istanza esistente (modalità modifica)...
        if self.instance and self.instance.pk:
            # ...e se i campi data hanno un valore...
            if self.instance.data_assunzione:
                # ...impostiamo il valore iniziale del form con la data formattata in ISO.
                self.initial['data_assunzione'] = self.instance.data_assunzione.strftime('%Y-%m-%d')
            if self.instance.data_fine_rapporto:
                self.initial['data_fine_rapporto'] = self.instance.data_fine_rapporto.strftime('%Y-%m-%d')

    def clean_mansione(self):
        data = self.cleaned_data.get('mansione')
        return data.upper() if data else data
    
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
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            # Popoliamo i queryset con i dati del tenant corrente
            self.fields['modalita_pagamento'].queryset = ModalitaPagamento.objects.filter(tenant=tenant, attivo=True)
            self.fields['cantiere'].queryset = Cantiere.objects.filter(tenant=tenant, attivo=True)
        # Inizializziamo l'anagrafica a vuoto, verrà popolata da JS
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
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        queryset = AliquotaIVA.objects.filter(attivo=True)
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        self.fields['aliquota_iva'].queryset = queryset

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
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        queryset = ContoFinanziario.objects.filter(attivo=True)
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        self.fields['conto_finanziario'].queryset = queryset

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
        label="Tipo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    stato = forms.ChoiceField(
        choices=STATO_CHOICES, 
        required=False,
        label="Stato",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class DiarioAttivitaForm(forms.ModelForm):
    """
    Form per la pianificazione e consuntivazione delle attività giornaliere.
    """
    class Meta:
        model = DiarioAttivita
        fields = [
            'cantiere_pianificato', 'mezzo_pianificato',
            'stato_presenza', 'tipo_assenza_giustificata',
            'ore_ordinarie', 'ore_straordinarie', 'note_giornaliere'
        ]
        widgets = {
            'cantiere_pianificato': forms.Select(attrs={'class': 'form-select'}),
            'mezzo_pianificato': forms.Select(attrs={'class': 'form-select'}),
            'stato_presenza': forms.Select(attrs={'class': 'form-select'}),
            'tipo_assenza_giustificata': forms.TextInput(attrs={'class': 'form-control'}),
            'ore_ordinarie': forms.NumberInput(attrs={'class': 'form-control'}),
            'ore_straordinarie': forms.NumberInput(attrs={'class': 'form-control'}),
            'note_giornaliere': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['cantiere_pianificato'].queryset = Cantiere.objects.filter(tenant=tenant, stato=Cantiere.Stato.APERTO)
            self.fields['mezzo_pianificato'].queryset = MezzoAziendale.objects.filter(tenant=tenant, attivo=True)

class DocumentoFilterForm(forms.Form):
    """
    Form per i filtri della lista documenti.
    """
    # Creiamo le scelte per il menu a tendina, includendo un'opzione vuota per "Tutti".
    TIPO_CHOICES = (
        ('', 'Tutti i Tipi'),
        (DocumentoTestata.TipoDoc.FATTURA_VENDITA, 'Fatture di Vendita'),
        (DocumentoTestata.TipoDoc.NOTA_CREDITO_VENDITA, 'Note di Credito di Vendita'),
        (DocumentoTestata.TipoDoc.FATTURA_ACQUISTO, 'Fatture di Acquisto'),
        (DocumentoTestata.TipoDoc.NOTA_CREDITO_ACQUISTO, 'Note di Credito di Acquisto'),
    )

    tipo_doc = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        label="Tipo Documento",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    data_da = forms.DateField(
        required=False, 
        label="Data Documento Da",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_a = forms.DateField(
        required=False, 
        label="Data Documento A",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class PrimaNotaFilterForm(forms.Form):
    """
    Form per i filtri della lista di Prima Nota.
    """
    descrizione = forms.CharField(
        required=False,
        label="Cerca Descrizione",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    conto_finanziario = forms.ModelChoiceField(
        queryset=ContoFinanziario.objects.filter(attivo=True),
        required=False,
        label="Conto Finanziario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    causale = forms.ModelChoiceField(
        queryset=Causale.objects.filter(attivo=True),
        required=False,
        label="Causale",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    data_da = forms.DateField(
        required=False, 
        label="Dal",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_a = forms.DateField(
        required=False, 
        label="Al",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class PrimaNotaForm(forms.ModelForm):
    conto_destinazione = forms.ModelChoiceField(
        queryset=ContoFinanziario.objects.filter(attivo=True),
        required=False,
        label="Conto Finanziario di Destinazione",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = PrimaNota
        fields = [
            'causale', 
            'data_registrazione', 'descrizione', 'importo', 'tipo_movimento',
            'conto_finanziario', 'conto_destinazione',
            'conto_operativo', 'anagrafica', 'cantiere'
        ]
        widgets = {
            'causale': forms.Select(attrs={'class': 'form-select'}),
            'data_registrazione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descrizione': forms.TextInput(attrs={'class': 'form-control'}),
            'importo': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo_movimento': forms.Select(attrs={'class': 'form-select'}),            
            'conto_finanziario': forms.Select(attrs={'class': 'form-select'}),
            'conto_operativo': forms.Select(attrs={'class': 'form-select'}),
            'anagrafica': forms.Select(attrs={'class': 'form-select'}),
            'cantiere': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        # Ottimizziamo i queryset per i menu a tendina
        if tenant:
            self.fields['conto_finanziario'].queryset = ContoFinanziario.objects.filter(tenant=tenant, attivo=True)
            self.fields['conto_operativo'].queryset = ContoOperativo.objects.filter(tenant=tenant, attivo=True)
            self.fields['causale'].queryset = Causale.objects.filter(tenant=tenant, attivo=True)
            self.fields['anagrafica'].queryset = Anagrafica.objects.filter(tenant=tenant, attivo=True)
            self.fields['cantiere'].queryset = Cantiere.objects.filter(tenant=tenant, stato=Cantiere.Stato.APERTO)
            self.fields['conto_destinazione'].queryset = ContoFinanziario.objects.filter(tenant=tenant, attivo=True)
        
        # Rendiamo il tipo_movimento non obbligatorio a livello di form.
        # La sua obbligatorietà verrà gestita nella logica del metodo clean().
        self.fields['tipo_movimento'].required = False
        
        # Aggiungiamo un'opzione vuota per permettere la selezione iniziale
        # e per evitare che il browser pre-selezioni un valore.
        self.fields['tipo_movimento'].choices = [('', '---------')] + list(self.fields['tipo_movimento'].choices)


    def clean(self):
        """
        Validazione incrociata per il giroconto e i movimenti standard.
        """
        cleaned_data = super().clean()
        causale = cleaned_data.get('causale')
        tipo_movimento = cleaned_data.get('tipo_movimento')

        try:
            causale_giroconto = Causale.objects.get(descrizione__iexact="GIROCONTO")
        except Causale.DoesNotExist:
            causale_giroconto = None

        # CASO 1: È un giroconto
        if causale and causale == causale_giroconto:
            conto_finanziario = cleaned_data.get('conto_finanziario')
            conto_destinazione = cleaned_data.get('conto_destinazione')
            
            if not conto_destinazione:
                self.add_error('conto_destinazione', 'Questo campo è obbligatorio per un giroconto.')
            
            if conto_finanziario and conto_destinazione and conto_finanziario == conto_destinazione:
                self.add_error('conto_destinazione', 'Il conto di destinazione non può essere uguale a quello di origine.')
            
            # Per un giroconto, il tipo_movimento non è richiesto dal form,
            # quindi non lo validiamo qui. Verrà impostato nella vista.

        # CASO 2: NON è un giroconto
        else:
            # Per tutti gli altri movimenti, il tipo_movimento è obbligatorio.
            if not tipo_movimento:
                self.add_error('tipo_movimento', 'Questo campo è obbligatorio.')
                
        return cleaned_data

class PartitarioFilterForm(forms.Form):
    """
    Form per i filtri di data del Partitario Anagrafica.
    """
    data_da = forms.DateField(
        required=False,
        label="Dal",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_a = forms.DateField(
        required=False,
        label="Al",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class PrimaNotaUpdateForm(PrimaNotaForm): # Eredita dal form di creazione
    """
    Form specifico per la MODIFICA di un movimento di Prima Nota.
    Gestisce la formattazione corretta della data.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se stiamo modificando un'istanza esistente e la data c'è...
        if self.instance and self.instance.data_registrazione:
            # ...formattiamo la data nel formato che il widget HTML si aspetta.
            self.initial['data_registrazione'] = self.instance.data_registrazione.strftime('%Y-%m-%d')

class PagamentoUpdateForm(forms.ModelForm):
    """
    Form per la MODIFICA di un pagamento esistente (PrimaNota).
    Include una validazione custom per l'importo.
    """
    class Meta:
        model = PrimaNota
        fields = ['data_registrazione', 'importo', 'conto_finanziario']
        widgets = {
            'data_registrazione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'importo': forms.NumberInput(attrs={'class': 'form-control'}),
            'conto_finanziario': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        # ... (logica formattazione data)
        queryset = ContoFinanziario.objects.filter(attivo=True)
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        self.fields['conto_finanziario'].queryset = queryset

    def clean_importo(self):
        """
        Validazione per assicurarsi che il nuovo importo sia valido.
        """
        importo_nuovo = self.cleaned_data.get('importo')
        if importo_nuovo <= 0:
            raise forms.ValidationError("L'importo deve essere maggiore di zero.")

        # self.instance è il pagamento ORIGINALE, prima delle modifiche
        scadenza = self.instance.scadenza_collegata
        importo_originale_pagamento = self.instance.importo
        
        # Calcoliamo il totale già pagato sulla scadenza, ESCLUSO questo pagamento
        # Aggiungiamo output_field=models.DecimalField() a Coalesce
        totale_altri_pagamenti = scadenza.pagamenti.exclude(pk=self.instance.pk).aggregate(
            total=Coalesce(Sum('importo'), Value(0), output_field=models.DecimalField())
        )['total']
        
        # Il massimo importo che questo pagamento può assumere
        massimo_importo_consentito = scadenza.importo_rata - totale_altri_pagamenti

        if importo_nuovo > massimo_importo_consentito:
            raise forms.ValidationError(
                f"L'importo supera il residuo della scadenza. Massimo consentito: € {massimo_importo_consentito:.2f}"
            )
        
        return importo_nuovo
    
class ModalitaPagamentoForm(forms.ModelForm):
    """
    Form per la creazione e modifica delle Modalità di Pagamento.
    """
    class Meta:
        model = ModalitaPagamento
        fields = ['descrizione', 'giorni_scadenza', 'attivo']
        widgets = {
            'descrizione': forms.TextInput(attrs={'class': 'form-control'}),
            'giorni_scadenza': forms.NumberInput(attrs={'class': 'form-control'}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_descrizione(self):
        # Applichiamo la sanificazione per coerenza
        data = self.cleaned_data.get('descrizione')
        return data.upper() if data else data
    
class AliquotaIVAForm(forms.ModelForm):
    """
    Form per la creazione e modifica delle Aliquote IVA.
    """
    class Meta:
        model = AliquotaIVA
        fields = ['descrizione', 'valore_percentuale', 'attivo']
        widgets = {
            'descrizione': forms.TextInput(attrs={'class': 'form-control'}),
            'valore_percentuale': forms.NumberInput(attrs={'class': 'form-control'}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_descrizione(self):
        data = self.cleaned_data.get('descrizione')
        return data.upper() if data else data
    
class CausaleForm(forms.ModelForm):
    """
    Form per la creazione e modifica delle Causali Contabili.
    """
    class Meta:
        model = Causale
        # === CORREZIONE: usiamo il nome del campo corretto 'tipo_movimento_default' ===
        fields = ['descrizione', 'tipo_movimento_default', 'attivo']
        
        widgets = {
            'descrizione': forms.TextInput(attrs={'class': 'form-control'}),
            # Usiamo il nome corretto anche qui
            'tipo_movimento_default': forms.Select(attrs={'class': 'form-select'}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_descrizione(self):
        data = self.cleaned_data.get('descrizione')
        return data.upper() if data else data

class ContoFinanziarioForm(forms.ModelForm):
    """
    Form per la creazione e modifica dei Conti Finanziari.
    """
    class Meta:
        model = ContoFinanziario
        fields = ['nome_conto', 'attivo']
        widgets = {
            'nome_conto': forms.TextInput(attrs={'class': 'form-control'}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nome_conto(self):
        data = self.cleaned_data.get('nome_conto')
        return data.upper() if data else data
    
class ContoOperativoForm(forms.ModelForm):
    """
    Form per la creazione e modifica dei Conti Operativi.
    """
    class Meta:
        model = ContoOperativo
        fields = ['nome_conto', 'tipo', 'attivo']
        widgets = {
            'nome_conto': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nome_conto(self):
        data = self.cleaned_data.get('nome_conto')
        return data.upper() if data else data

class MezzoAziendaleForm(forms.ModelForm):
    """
    Form per la creazione e modifica dei Mezzi Aziendali.
    """
    class Meta:
        model = MezzoAziendale
        fields = ['targa', 'descrizione', 'tipo', 'attivo']
        widgets = {
            'targa': forms.TextInput(attrs={'class': 'form-control'}),
            'descrizione': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control'}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_targa(self):
        data = self.cleaned_data.get('targa')
        return data.replace(" ", "").upper() if data else data
    
    def clean_descrizione(self):
        data = self.cleaned_data.get('descrizione')
        return data.upper() if data else data
    
    def clean_tipo(self):
        data = self.cleaned_data.get('tipo')
        return data.upper() if data else data

class TipoScadenzaPersonaleForm(forms.ModelForm):
    """
    Form per la creazione e modifica dei Tipi di Scadenze Personale.
    """
    class Meta:
        model = TipoScadenzaPersonale
        fields = ['descrizione', 'validita_mesi', 'note', 'attivo']
        widgets = {
            'descrizione': forms.TextInput(attrs={'class': 'form-control'}),
            'validita_mesi': forms.NumberInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_descrizione(self):
        data = self.cleaned_data.get('descrizione')
        return data.upper() if data else data
    
class ScadenzaPersonaleForm(forms.ModelForm):
    """
    Form per la creazione e modifica delle Scadenze Personali.
    """
    class Meta:
        model = ScadenzaPersonale
        # Escludiamo i campi gestiti automaticamente (dipendente, created_by, etc.)
        fields = ['tipo_scadenza', 'data_esecuzione', 'data_scadenza', 'stato', 'note']
        widgets = {
            'tipo_scadenza': forms.Select(attrs={'class': 'form-select'}),
            'data_esecuzione': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_scadenza': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'stato': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Inizializzazione personalizzata per:
        - Popolare il queryset del tipo scadenza.
        - Formattare correttamente le date iniziali per il widget HTML.
        """
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['tipo_scadenza'].queryset = TipoScadenzaPersonale.objects.filter(tenant=tenant, attivo=True)

        # === INIZIO CORREZIONE ===
        # Se il form è legato a un'istanza esistente (siamo in modalità modifica)...
        if self.instance and self.instance.pk:
            # ...e se i campi data hanno un valore...
            if self.instance.data_esecuzione:
                # ...impostiamo il valore iniziale del form con la data formattata in ISO.
                self.initial['data_esecuzione'] = self.instance.data_esecuzione.strftime('%Y-%m-%d')
            if self.instance.data_scadenza:
                self.initial['data_scadenza'] = self.instance.data_scadenza.strftime('%Y-%m-%d')
        # === FINE CORREZIONE ===

class CantiereForm(forms.ModelForm):
    """
    Form per la creazione e modifica dei Cantieri.
    """
    class Meta:
        model = Cantiere
        fields = [
            'codice_cantiere', 'descrizione', 'indirizzo', 'cliente',
            'data_inizio', 'data_fine_prevista', 'stato', 'attivo'
        ]
        # Aggiorniamo i widget per aggiungere il placeholder
        widgets = {
            'codice_cantiere': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Es: C-2025-MILANO-001'
            }),
            'descrizione': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'indirizzo': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'data_inizio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fine_prevista': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'stato': forms.Select(attrs={'class': 'form-select'}),
            'attivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['cliente'].queryset = Anagrafica.objects.filter(tenant=tenant, tipo=Anagrafica.Tipo.CLIENTE, attivo=True)
        if self.instance and self.instance.pk:
            if self.instance.data_inizio:
                self.initial['data_inizio'] = self.instance.data_inizio.strftime('%Y-%m-%d')
            if self.instance.data_fine_prevista:
                self.initial['data_fine_prevista'] = self.instance.data_fine_prevista.strftime('%Y-%m-%d')

    # === METODI DI SANIFICAZIONE AGGIUNTI ===
    def clean_codice_cantiere(self):
        data = self.cleaned_data.get('codice_cantiere')
        return data.upper() if data else data

    def clean_descrizione(self):
        data = self.cleaned_data.get('descrizione')
        return data.upper() if data else data

    def clean_indirizzo(self):
        data = self.cleaned_data.get('indirizzo')
        return data.upper() if data else data

class FascicoloCantiereFilterForm(forms.Form):
    """
    Form per i filtri di data del Fascicolo Cantiere.
    """
    data_da = forms.DateField(
        required=False,
        label="Dal",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_a = forms.DateField(
        required=False,
        label="Al",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class AnalisiFilterForm(forms.Form):
    """
    Form per i filtri di data della Dashboard di Analisi.
    """
    data_da = forms.DateField(
        required=False,
        label="Dal",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_a = forms.DateField(
        required=False,
        label="Al",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


