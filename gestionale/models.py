# gestionale/models.py

from django.db import models, transaction
from django.conf import settings
from django.urls import reverse # Per riferirci al nostro User model personalizzato
from tenants.models import Company
from .managers import TenantAwareManager

class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_related')

    objects = TenantAwareManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        from .managers import get_current_tenant
        if not self.pk:
            if not self.tenant_id:
                current_tenant = get_current_tenant()
                if current_tenant:
                    self.tenant = current_tenant
                else:
                    # Questo dovrebbe essere gestito dal middleware o dalla vista
                    # ma è un fallback di sicurezza per evitare IntegrityError
                    raise Exception("Cannot save tenant-aware model without a current tenant set.")
        super().save(*args, **kwargs)

# ==============================================================================
# === MODELLI DI CONFIGURAZIONE (Tabelle di supporto)                       ===
# ==============================================================================
# Questi modelli contengono le opzioni che popolano i menu a tendina
# nel resto dell'applicazione (es. aliquote IVA, modalità di pagamento).

class AliquotaIVA(models.Model):
    descrizione = models.CharField(max_length=100, verbose_name="Descrizione")
    valore_percentuale = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Valore %")
    attivo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.descrizione} ({self.valore_percentuale}%)"

    class Meta:
        verbose_name = "Aliquota IVA"
        verbose_name_plural = "Aliquote IVA"
        ordering = ['valore_percentuale'] # Ordina le aliquote per valore

class ModalitaPagamento(models.Model):
    descrizione = models.CharField(max_length=100, unique=True, verbose_name="Descrizione")
    giorni_scadenza = models.IntegerField(default=30, verbose_name="Giorni a scadere di default")
    attivo = models.BooleanField(default=True)

    def __str__(self):
        return self.descrizione

    class Meta:
        verbose_name = "Modalità di Pagamento"
        verbose_name_plural = "Modalità di Pagamento"
        ordering = ['descrizione']

class Causale(models.Model):
    descrizione = models.CharField(max_length=255, unique=True)
    # Potremmo usare delle choices anche qui, ma per ora un testo libero è sufficiente.
    tipo_movimento = models.CharField(max_length=50, blank=True, null=True, help_text="Es: Pagamento Fattura, Incasso, Costo")
    attivo = models.BooleanField(default=True)

    def __str__(self):
        return self.descrizione
    class Meta:
        verbose_name = "Causale"
        verbose_name_plural = "Causali"

class ContoFinanziario(TenantAwareModel):
    nome_conto = models.CharField(max_length=100, unique=True, verbose_name="Nome Conto")
    attivo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome_conto
    class Meta:
        verbose_name = "Conto Finanziario"
        verbose_name_plural = "Conti Finanziari"

class ContoOperativo(TenantAwareModel):
    class Tipo(models.TextChoices):
        COSTO = 'Costo', 'Costo'
        RICAVO = 'Ricavo', 'Ricavo'

    nome_conto = models.CharField(max_length=100, unique=True, verbose_name="Nome Conto")
    tipo = models.CharField(max_length=10, choices=Tipo.choices, verbose_name="Tipo")
    attivo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome_conto} ({self.tipo})"
    class Meta:
        verbose_name = "Conto Operativo"
        verbose_name_plural = "Conti Operativi"

class MezzoAziendale(models.Model):
    targa = models.CharField(max_length=20, unique=True)
    descrizione = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, blank=True, null=True, help_text="Es: Furgone, Autovettura, Escavatore")
    attivo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.descrizione} ({self.targa})"
    class Meta:
        verbose_name = "Mezzo Aziendale"
        verbose_name_plural = "Mezzi Aziendali"

class TipoScadenzaPersonale(models.Model):
    descrizione = models.CharField(max_length=100, unique=True)
    validita_mesi = models.IntegerField(null=True, blank=True, help_text="Numero di mesi di validità. Lasciare vuoto se non applicabile.")
    note = models.TextField(blank=True, null=True)
    attivo = models.BooleanField(default=True)

    def __str__(self):
        return self.descrizione
    class Meta:
        verbose_name = "Tipo Scadenza Personale"
        verbose_name_plural = "Tipi Scadenze Personale"


# ==============================================================================
# === MODELLI CORE (Anagrafiche, Cantieri)                                  ===
# ==============================================================================

class Anagrafica(TenantAwareModel):
    class Tipo(models.TextChoices):
        CLIENTE = 'Cliente', 'Cliente'
        FORNITORE = 'Fornitore', 'Fornitore'
        DIPENDENTE = 'Dipendente', 'Dipendente'

    codice = models.CharField(max_length=20, verbose_name="Codice Anagrafica", blank=True, editable=False)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, verbose_name="Tipo Anagrafica")
    nome_cognome_ragione_sociale = models.CharField(max_length=255, verbose_name="Nome/Cognome o Ragione Sociale")
    p_iva = models.CharField(max_length=16, blank=True, null=True, verbose_name="Partita IVA")
    codice_fiscale = models.CharField(max_length=16, blank=True, null=True, verbose_name="Codice Fiscale")
    indirizzo = models.CharField(max_length=255, blank=True, null=True)
    cap = models.CharField(max_length=10, blank=True, null=True, verbose_name="CAP")
    citta = models.CharField(max_length=100, blank=True, null=True, verbose_name="Città")
    provincia = models.CharField(max_length=2, blank=True, null=True, verbose_name="Provincia")
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    attivo = models.BooleanField(default=True)

    # Campi di tracciamento
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # models.SET_NULL: se l'utente che ha creato il record viene cancellato,
    # il campo 'created_by' diventa NULL invece di cancellare anche l'anagrafica.
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='anagrafiche_create', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='anagrafiche_aggiornate', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nome_cognome_ragione_sociale} ({self.codice})"
    
    # === NUOVO METODO SAVE  ===
    def save(self, *args, **kwargs):
        """
        Sovrascrive il metodo save per generare il codice anagrafica
        automaticamente al primo salvataggio.
        """
        # La logica di generazione del codice deve essere eseguita solo
        # se l'oggetto è nuovo (non ha ancora un 'pk') E non ha già un codice.
        if not self.pk or not self.codice:
            tipo = self.tipo
            prefisso = {
                self.Tipo.CLIENTE: 'CL',
                self.Tipo.FORNITORE: 'FO',
                self.Tipo.DIPENDENTE: 'DI'
            }.get(tipo, 'XX')

            last_anagrafica = Anagrafica.objects.filter(tipo=tipo).order_by('codice').last()
            
            if last_anagrafica and last_anagrafica.codice:
                last_number = int(last_anagrafica.codice[2:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.codice = f"{prefisso}{new_number:06d}"
            
        # Chiama il metodo save() originale per eseguire il salvataggio effettivo
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Anagrafica"
        verbose_name_plural = "Anagrafiche"
        ordering = ['nome_cognome_ragione_sociale']

class Cantiere(TenantAwareModel):
    class Stato(models.TextChoices):
        BOZZA = 'Bozza', 'Bozza'
        APERTO = 'Aperto', 'Aperto'
        SOSPESO = 'Sospeso', 'Sospeso'
        CHIUSO = 'Chiuso', 'Chiuso'

    codice_cantiere = models.CharField(max_length=50, unique=True, verbose_name="Codice Cantiere")
    descrizione = models.CharField(max_length=255, verbose_name="Descrizione")
    indirizzo = models.CharField(max_length=255, blank=True, null=True)
    # Limita la scelta del cliente solo alle anagrafiche di tipo 'Cliente'
    cliente = models.ForeignKey(Anagrafica, on_delete=models.PROTECT, limit_choices_to={'tipo': Anagrafica.Tipo.CLIENTE}, verbose_name="Cliente")
    data_inizio = models.DateField(null=True, blank=True, verbose_name="Data Inizio Lavori")
    data_fine_prevista = models.DateField(null=True, blank=True, verbose_name="Data Fine Prevista")
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.BOZZA)
    attivo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='cantieri_creati', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='cantieri_aggiornati', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.codice_cantiere} - {self.descrizione}"

    class Meta:
        verbose_name = "Cantiere"
        verbose_name_plural = "Cantieri"
        ordering = ['-data_inizio', 'codice_cantiere']


# ==============================================================================
# === MODELLI CONTABILI (Documenti, Scadenze, Prima Nota)                   ===
# ==============================================================================

class DocumentoTestata(TenantAwareModel):
    class TipoDoc(models.TextChoices):
        FATTURA_VENDITA = 'FTV', 'Fattura di Vendita'
        NOTA_CREDITO_VENDITA = 'NCV', 'Nota di Credito di Vendita'
        FATTURA_ACQUISTO = 'FTA', 'Fattura di Acquisto'
        NOTA_CREDITO_ACQUISTO = 'NCA', 'Nota di Credito di Acquisto'

    class Stato(models.TextChoices):
        BOZZA = 'Bozza', 'Bozza'
        CONFERMATO = 'Confermato', 'Confermato'
        ANNULLATO = 'Annullato', 'Annullato'

    tipo_doc = models.CharField(max_length=10, choices=TipoDoc.choices, verbose_name="Tipo Documento")
    # related_name ci permette di accedere ai documenti di un'anagrafica in modo facile
    # da un oggetto anagrafica: anagrafica.documenti.all()
    anagrafica = models.ForeignKey(Anagrafica, on_delete=models.PROTECT, related_name='documenti', verbose_name="Cliente/Fornitore")
    modalita_pagamento = models.ForeignKey(ModalitaPagamento, on_delete=models.PROTECT, verbose_name="Modalità di Pagamento")
    cantiere = models.ForeignKey(Cantiere, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cantiere Associato")

    data_documento = models.DateField(verbose_name="Data Documento")
    numero_documento = models.CharField(max_length=50, verbose_name="Numero Documento")
    
    # Per i campi monetari, DecimalField è SEMPRE la scelta migliore rispetto a FloatField.
    # Evita problemi di arrotondamento. max_digits è il numero totale di cifre,
    # decimal_places è il numero di cifre dopo la virgola.
    imponibile = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="IVA")
    totale = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Per le note di credito, questo campo legherà la NC alla fattura originale.
    # 'self' indica una relazione sulla stessa tabella.
    fattura_collegata = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fattura Collegata")
    note = models.TextField(blank=True, null=True)
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.BOZZA)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='documenti_creati', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='documenti_aggiornati', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.get_tipo_doc_display()} N. {self.numero_documento} del {self.data_documento}"

    def get_absolute_url(self):
        """
        Restituisce l'URL canonico per un'istanza di questo modello.
        """
        return reverse('documento_detail', kwargs={'pk': self.pk})
    class Meta:
        verbose_name = "Documento (Testata)"
        verbose_name_plural = "Documenti (Testate)"
        unique_together = ('anagrafica', 'tipo_doc', 'numero_documento')
        ordering = ['-data_documento', '-numero_documento']


class DocumentoRiga(models.Model):
    testata = models.ForeignKey(DocumentoTestata, on_delete=models.CASCADE, related_name='righe', verbose_name="Testata Documento")
    descrizione = models.CharField(max_length=255)
    quantita = models.DecimalField(max_digits=10, decimal_places=2, default=1.00, verbose_name="Quantità")
    prezzo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    aliquota_iva = models.ForeignKey(AliquotaIVA, on_delete=models.PROTECT, verbose_name="Aliquota IVA")
    
    imponibile_riga = models.DecimalField(max_digits=10, decimal_places=2)
    iva_riga = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="IVA Riga")

    def __str__(self):
        return self.descrizione

    class Meta:
        verbose_name = "Riga Documento"
        verbose_name_plural = "Righe Documenti"

class Scadenza(TenantAwareModel):
    class Stato(models.TextChoices):
        APERTA = 'Aperta', 'Aperta'
        PARZIALE = 'Parziale', 'Pagata Parzialmente'
        SALDATA = 'Saldata', 'Saldata'
        ANNULLATA = 'Annullata', 'Annullata'
    
    class Tipo(models.TextChoices):
        INCASSO = 'Incasso', 'Incasso da Cliente'
        PAGAMENTO = 'Pagamento', 'Pagamento a Fornitore'

    documento = models.ForeignKey(DocumentoTestata, on_delete=models.CASCADE, related_name='scadenze')
    anagrafica = models.ForeignKey(Anagrafica, on_delete=models.PROTECT, related_name='scadenze')
    data_scadenza = models.DateField(verbose_name="Data di Scadenza")
    importo_rata = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Importo Rata")
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.APERTA)
    tipo_scadenza = models.CharField(max_length=20, choices=Tipo.choices)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NOTA: La logica per 'importo_pagato' e 'importo_residuo' che avevi nella
    # reference la implementeremo in modo più "Djangonico" direttamente nelle viste
    # o con delle properties del modello quando necessario. L'ORM di Django è così
    # potente che spesso non serve pre-calcolare questi valori a livello di DB.

    def __str__(self):
        return f"Scadenza {self.id} - {self.anagrafica.nome_cognome_ragione_sociale} - €{self.importo_rata}"
    
    class Meta:
        verbose_name = "Scadenza"
        verbose_name_plural = "Scadenze"
        ordering = ['data_scadenza']


class PrimaNota(TenantAwareModel):
    class TipoMovimento(models.TextChoices):
        ENTRATA = 'E', 'Entrata'
        USCITA = 'U', 'Uscita'

    data_registrazione = models.DateField()
    descrizione = models.CharField(max_length=255, verbose_name="Descrizione Movimento")
    importo = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_movimento = models.CharField(max_length=1, choices=TipoMovimento.choices)
    
    conto_finanziario = models.ForeignKey(ContoFinanziario, on_delete=models.PROTECT, related_name='movimenti', verbose_name="Conto Finanziario")
    conto_operativo = models.ForeignKey(ContoOperativo, on_delete=models.PROTECT, null=True, blank=True, related_name='movimenti', verbose_name="Conto Operativo (Costo/Ricavo)")
    causale = models.ForeignKey(Causale, on_delete=models.PROTECT, related_name='movimenti', verbose_name="Causale")
    anagrafica = models.ForeignKey(Anagrafica, on_delete=models.PROTECT, null=True, blank=True, related_name='movimenti_primanota')
    cantiere = models.ForeignKey(Cantiere, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimenti_primanota')
    scadenza_collegata = models.ForeignKey(Scadenza, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagamenti')

    # Collega due movimenti di Prima Nota tra loro (usato per i giroconti).
    # La relazione è a 'self', cioè a un altro record della stessa tabella.
    movimento_collegato = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, # Se cancello un movimento, l'altro non viene cancellato ma il legame si spezza.
        null=True, 
        blank=True,
        related_name='movimento_speculare'
    )
    # === FINE CAMPO AGGIUNTO ===

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='primanota_create', on_delete=models.SET_NULL, null=True, blank=True)
    

    def __str__(self):
        return f"{self.data_registrazione} - {self.descrizione} - €{self.importo}"

    class Meta:
        verbose_name = "Prima Nota"
        verbose_name_plural = "Prima Nota"
        ordering = ['data_registrazione', 'pk'] # Aggiunto '-pk' per coerenza


class DipendenteDettaglio(models.Model):
    anagrafica = models.OneToOneField(Anagrafica, on_delete=models.CASCADE, primary_key=True, related_name='dettaglio_dipendente', limit_choices_to={'tipo': Anagrafica.Tipo.DIPENDENTE})
    mansione = models.CharField(max_length=100)
    data_assunzione = models.DateField()
    data_fine_rapporto = models.DateField(null=True, blank=True)
    
    ore_settimanali_contratto = models.DecimalField(
        max_digits=4, decimal_places=2, default=40.00, 
        verbose_name="Ore Settimanali da Contratto"
    )
    giorni_lavorativi_settimana = models.IntegerField(
        default=5, 
        verbose_name="Giorni Lavorativi a Settimana"
    )
    
    costo_orario = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)
    note_generali = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.anagrafica.nome_cognome_ragione_sociale

    # === NUOVO METODO AGGIUNTO ===
    def save(self, *args, **kwargs):
        """
        Sovrascrive il metodo di salvataggio per automatizzare lo stato 'attivo'
        dell'anagrafica collegata in base alla data di fine rapporto.
        """
        # Caso 1: Viene inserita una data di fine rapporto.
        # Il dipendente associato deve essere disattivato.
        if self.data_fine_rapporto:
            self.anagrafica.attivo = False
        
        # Caso 2: La data di fine rapporto viene rimossa (es. riassunzione).
        # Il dipendente associato deve essere riattivato.
        else:
            self.anagrafica.attivo = True

        # Dopo aver impostato lo stato, salviamo l'anagrafica collegata.
        self.anagrafica.save()
        
        # Infine, chiamiamo il metodo save() originale della classe genitore
        # per salvare l'oggetto DipendenteDettaglio stesso.
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Dettaglio Dipendente"
        verbose_name_plural = "Dettagli Dipendenti"


class DiarioAttivita(models.Model):
    class StatoPresenza(models.TextChoices):
        PRESENTE = 'Presente', 'Presente'
        ASSENTE_G = 'Assente Giustificato', 'Assente Giustificato'
        ASSENTE_I = 'Assente Ingiustificato', 'Assente Ingiustificato'
    
    data = models.DateField()
    dipendente = models.ForeignKey(Anagrafica, on_delete=models.PROTECT, related_name='diario', limit_choices_to={'tipo': Anagrafica.Tipo.DIPENDENTE})
    
    # Pianificazione
    cantiere_pianificato = models.ForeignKey(Cantiere, on_delete=models.SET_NULL, null=True, blank=True, related_name='personale_pianificato')
    mezzo_pianificato = models.ForeignKey(MezzoAziendale, on_delete=models.SET_NULL, null=True, blank=True, related_name='utilizzi_pianificati')
    
    # Consuntivo
    stato_presenza = models.CharField(max_length=30, choices=StatoPresenza.choices, null=True, blank=True)
    tipo_assenza_giustificata = models.CharField(max_length=100, blank=True, null=True, help_text="Es: Ferie, Malattia, Permesso")
    ore_ordinarie = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    ore_straordinarie = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    costo_orario_consuntivo = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Costo orario del giorno, se diverso dallo standard")
    note_giornaliere = models.TextField(blank=True, null=True)

    # === CAMPI DI TRACCIABILITÀ AGGIUNTI/COMPLETATI ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='diario_creati', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        # editable=False per non mostrarlo nei form
        editable=False 
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='diario_aggiornati',
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        editable=False
    )
    # === FINE CAMPI  ===

    def __str__(self):
        return f"Diario del {self.data} per {self.dipendente.nome_cognome_ragione_sociale}"

    class Meta:
        verbose_name = "Diario Attività"
        verbose_name_plural = "Diari Attività"
        # Un dipendente può avere una sola riga di diario per un dato giorno
        unique_together = ('data', 'dipendente')
        ordering = ['-data', 'dipendente']


class ScadenzaPersonale(models.Model):
    class Stato(models.TextChoices):
        VALIDA = 'Valida', 'Valida'
        SCADUTA = 'Scaduta', 'Scaduta'
        RINNOVATA = 'Rinnovata', 'Rinnovata'

    dipendente = models.ForeignKey(Anagrafica, on_delete=models.CASCADE, related_name='scadenze_personali', limit_choices_to={'tipo': Anagrafica.Tipo.DIPENDENTE})
    tipo_scadenza = models.ForeignKey(TipoScadenzaPersonale, on_delete=models.PROTECT)
    data_esecuzione = models.DateField()
    data_scadenza = models.DateField()
    stato = models.CharField(max_length=20, choices=Stato.choices, default=Stato.VALIDA)
    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.tipo_scadenza.descrizione} di {self.dipendente.nome_cognome_ragione_sociale}"

    class Meta:
        verbose_name = "Scadenza Personale"
        verbose_name_plural = "Scadenze Personale"
        ordering = ['data_scadenza']