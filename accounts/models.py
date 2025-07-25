# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

# Un modello Django è una classe che eredita da models.Model.
# Per il nostro utente, ereditiamo da AbstractUser, che ci dà già tutti i campi
# standard di un utente (username, password, email, is_active, ecc.)
# senza doverli riscrivere. Noi dobbiamo solo aggiungere ciò che ci manca.
class User(AbstractUser):
    """
    Modello Utente personalizzato.
    Eredita tutti i campi di default di Django e aggiunge il system_role.
    """
    # Usiamo una classe 'TextChoices' per definire i ruoli possibili.
    # È una best practice perché rende il codice più leggibile e manutenibile,
    # e possiamo riusare SystemRole.SUPER_ADMIN in altre parti del codice
    # senza dover scrivere la stringa "super_admin" a mano.
    class SystemRole(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Amministratore'
        USER = 'user', 'Utente Standard'

    # Questo è il nostro campo personalizzato.
    # CharField è l'equivalente di un VARCHAR in SQL.
    system_role = models.CharField(
        max_length=20,
        choices=SystemRole.choices,
        default=SystemRole.USER,
        verbose_name="Ruolo di Sistema" # Etichetta per il pannello di amministrazione
    )

    # Nota: Il campo 'attivo' del tuo modello di riferimento è già presente in
    # AbstractUser e si chiama 'is_active'. Django ce lo fornisce gratuitamente!
    # Non abbiamo bisogno di ridefinirlo.