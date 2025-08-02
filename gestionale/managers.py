from django.db import models
from django.db.models.query import QuerySet
from threading import local

_current_tenant = local()

class TenantAwareQuerySet(QuerySet):
    def for_tenant(self, tenant):
        return self.filter(tenant=tenant)

class TenantAwareManager(models.Manager):
    def get_queryset(self):
        # Filtra il queryset in base al tenant corrente
        tenant = get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenant=tenant)
        return super().get_queryset()

    def for_tenant(self, tenant):
        return self.get_queryset().for_tenant(tenant)

# Funzione per impostare il tenant corrente (usata dal middleware)
def set_current_tenant(tenant):
    _current_tenant.value = tenant

# Funzione per ottenere il tenant corrente (usata dal manager e dal modello)
def get_current_tenant():
    return getattr(_current_tenant, 'value', None)
