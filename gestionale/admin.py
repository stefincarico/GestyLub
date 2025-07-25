# gestionale/admin.py

from django.contrib import admin
from .models import (
    AliquotaIVA,
    ModalitaPagamento,
    Anagrafica,
    Cantiere,
    DocumentoTestata,
    DocumentoRiga
)

# Per ora, facciamo una registrazione semplice per ogni modello.
# In futuro, personalizzeremo queste viste per renderle più potenti.
admin.site.register(AliquotaIVA)
admin.site.register(ModalitaPagamento)
admin.site.register(Anagrafica)
admin.site.register(Cantiere)

# Per i modelli con relazioni (come Testata e Righe), Django offre
# un modo più elegante per visualizzarli, chiamato "Inline".
# Lo vedremo in una lezione successiva. Per ora, registriamoli separatamente.
admin.site.register(DocumentoTestata)
admin.site.register(DocumentoRiga)