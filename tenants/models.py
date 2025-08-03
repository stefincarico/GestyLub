# tenants/models.py

from django.db import models
from django.conf import settings # Importiamo settings per riferirci al nostro User personalizzato

class Company(models.Model):
    """
    Rappresenta una singola azienda cliente (tenant) sulla piattaforma.
    """
    company_name = models.CharField(max_length=255, unique=True, verbose_name="Nome Azienda")
    vat_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Partita IVA")
    is_active = models.BooleanField(default=True, verbose_name="Attiva")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creazione")

    def __str__(self):
        # Il metodo __str__ è molto importante. Fornisce una rappresentazione
        # "leggibile" dell'oggetto, utile nel pannello di amministrazione di Django.
        return self.company_name

    class Meta:
        # 'verbose_name_plural' definisce come Django deve chiamare la tabella al plurale.
        verbose_name = "Azienda"
        verbose_name_plural = "Aziende"


class UserCompanyPermission(models.Model):
    """
    Modello-ponte che collega un Utente a un'Azienda con un ruolo specifico.
    Questa è la tabella che implementa la relazione Many-to-Many con dati aggiuntivi.
    """
    class CompanyRole(models.TextChoices):
        ADMIN = 'admin', 'Amministratore'
        CONTABILE = 'contabile', 'Contabile'
        VISUALIZZATORE = 'visualizzatore', 'Visualizzatore'

    # ForeignKey crea una relazione "molti-a-uno".
    # Usiamo settings.AUTH_USER_MODEL invece di importare direttamente User
    # per evitare problemi di "dipendenze circolari". È la best practice.
    # on_delete=models.CASCADE significa che se un utente viene cancellato,
    # anche tutti i suoi permessi vengono cancellati.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Utente")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Azienda")

    company_role = models.CharField(
        max_length=20,
        choices=CompanyRole.choices,
        verbose_name="Ruolo Aziendale"
    )

    def __str__(self):
        return f"{self.user.username} - {self.company.company_name} ({self.get_company_role_display()})"

    class Meta:
        # Questa riga impone che la coppia (utente, azienda) sia unica.
        # Un utente non può avere due ruoli diversi per la stessa azienda.
        unique_together = ('user', 'company')
        verbose_name = "Permesso Utente-Azienda"
        verbose_name_plural = "Permessi Utente-Azienda"