# tenants/urls.py

from django.urls import path
from .views import TenantSelectionView

urlpatterns = [
    # Questo è l'URL che Django non riusciva a trovare prima!
    # Quando l'URL è 'select/', esegui la vista TenantSelectionView.
    # E, cosa più importante, gli diamo il nome 'tenant_selection'.
    path('select/', TenantSelectionView.as_view(), name='tenant_selection'),
]