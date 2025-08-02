from tenants.models import Company
from gestionale.managers import set_current_tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            active_tenant_id = request.session.get('active_tenant_id')
            if active_tenant_id:
                try:
                    tenant_obj = Company.objects.get(pk=active_tenant_id)
                    request.tenant = tenant_obj # Manteniamo per compatibilità con le viste
                    set_current_tenant(tenant_obj) # Imposta il tenant per il manager
                except Company.DoesNotExist:
                    request.tenant = None
                    set_current_tenant(None)
            else:
                request.tenant = None
                set_current_tenant(None)
        else:
            request.tenant = None # No tenant for unauthenticated users
            set_current_tenant(None)

        response = self.get_response(request)
        set_current_tenant(None) # Pulisce il tenant dopo la richiesta
        return response
