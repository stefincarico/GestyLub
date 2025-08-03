from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

# Creiamo la nostra vista di login personalizzata ereditando da quella di Django.
# Questo ci dà un sacco di funzionalità gratis (validazione del form, gestione errori, etc.)
# e ci permette di personalizzare solo ciò che ci serve.
class CustomLoginView(LoginView):
    # 1. Specifichiamo il template HTML che questa vista dovrà renderizzare.
    template_name = 'accounts/login.html'
    
    # 2. Impediamo a un utente già loggato di vedere di nuovo la pagina di login.
    #    Se ci prova, viene reindirizzato alla pagina specificata sotto.
    redirect_authenticated_user = True
    
    # 3. Definiamo dove mandare l'utente DOPO un login andato a buon fine.
    def get_success_url(self):
        """
        Reindirizza l'utente in base al suo ruolo di sistema.
        """
        # self.request.user è l'utente che ha appena fatto il login.
        if self.request.user.system_role == 'super_admin':
            # Se è un super_admin, lo mandiamo alla sua dashboard.
            return reverse_lazy('superadmin:dashboard')
        else:
            # Altrimenti, lo mandiamo alla selezione del tenant.
            return reverse_lazy('tenant_selection')