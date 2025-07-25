# gestionale/admin.py

from django.contrib import admin
# Importiamo tutti i modelli dalla nostra app
from .models import (
    AliquotaIVA,
    ModalitaPagamento,
    Anagrafica,
    Cantiere,
    DocumentoTestata,
    DocumentoRiga,
    # === MODELLI AGGIUNTI ===
    Causale,
    ContoFinanziario,
    ContoOperativo,
    MezzoAziendale,
    TipoScadenzaPersonale,
    Scadenza,
    PrimaNota,
    DipendenteDettaglio,
    DiarioAttivita,
    ScadenzaPersonale
)

# Registriamo tutti i modelli per renderli visibili nel pannello di amministrazione
admin.site.register(AliquotaIVA)
admin.site.register(ModalitaPagamento)
admin.site.register(Anagrafica)
admin.site.register(Cantiere)
admin.site.register(DocumentoTestata)
admin.site.register(DocumentoRiga)

# === REGISTRAZIONI AGGIUNTE ===
admin.site.register(Causale)
admin.site.register(ContoFinanziario)
admin.site.register(ContoOperativo)
admin.site.register(MezzoAziendale)
admin.site.register(TipoScadenzaPersonale)
admin.site.register(Scadenza)
admin.site.register(PrimaNota)
admin.site.register(DipendenteDettaglio)
admin.site.register(DiarioAttivita)
admin.site.register(ScadenzaPersonale)