# gestionale/models.py

from django.db import models
from django.conf import settings # Per riferirci al nostro User model personalizzato

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

# ... (Aggiungeremo gli altri modelli di configurazione qui man mano) ...

# ==============================================================================
# === MODELLI CORE (Anagrafiche, Cantieri)                                  ===
# ==============================================================================

class Anagrafica(models.Model):
    class Tipo(models.TextChoices):
        CLIENTE = 'Cliente', 'Cliente'
        FORNITORE = 'Fornitore', 'Fornitore'
        DIPENDENTE = 'Dipendente', 'Dipendente'

    codice = models.CharField(max_length=20, unique=True, verbose_name="Codice Anagrafica")
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

    class Meta:
        verbose_name = "Anagrafica"
        verbose_name_plural = "Anagrafiche"
        ordering = ['nome_cognome_ragione_sociale']

class Cantiere(models.Model):
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

class DocumentoTestata(models.Model):
    class TipoDoc(models.TextChoices):
        FATTURA_VENDITA = 'FTV', 'Fattura di Vendita'
        NOTA_CREDITO_VENDITA = 'NCV', 'Nota di Credito di Vendita'
        # Aggiungeremo altri tipi se necessario (es. Fatture Acquisto)

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
    
    class Meta:
        verbose_name = "Documento (Testata)"
        verbose_name_plural = "Documenti (Testate)"
        # Un'anagrafica non può avere due documenti dello stesso tipo con lo stesso numero
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