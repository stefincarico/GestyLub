# tenants/admin.py

from django.contrib import admin
from .models import Company, UserCompanyPermission

# La registrazione più semplice possibile.
# Dice a Django: "Mostra questo modello nel pannello di amministrazione".
admin.site.register(Company)
admin.site.register(UserCompanyPermission)