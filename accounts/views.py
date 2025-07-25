from django.contrib.auth.views import LoginView
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
    #    'reverse_lazy' è un modo intelligente per dire a Django: "Quando il login
    #    sarà completato, trova l'URL che ha come nome 'tenant_selection'".
    #    Definiremo questo nome tra poco nel nostro file urls.py.
    def get_success_url(self):
        return reverse_lazy('tenant_selection')