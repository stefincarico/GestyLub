# tenants/urls.py

from django.urls import path
from .views import ActivateTenantView, TenantSelectionView

urlpatterns = [
    # Questo è l'URL che Django non riusciva a trovare prima!
    # Quando l'URL è 'select/', esegui la vista TenantSelectionView.
    # E, cosa più importante, gli diamo il nome 'tenant_selection'.
    path('select/', TenantSelectionView.as_view(), name='tenant_selection'),
    
    # <int:company_id> è un "convertitore di percorso". Dice a Django di
    # aspettarsi un numero intero in questa parte dell'URL e di passarlo
    # alla vista come argomento chiamato 'company_id'.
    path('activate/<int:company_id>/', ActivateTenantView.as_view(), name='activate_tenant'),
]