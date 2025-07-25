# accounts/urls.py

from django.urls import path
from .views import CustomLoginView
from django.contrib.auth.views import LogoutView

# Questo è l'elenco degli URL specifici per questa app.
urlpatterns = [
    # Quando l'URL è 'login/', esegui la vista CustomLoginView.
    # 'as_view()' è necessario perché stiamo usando una vista basata su classi.
    # 'name="login"' assegna un nome univoco a questo URL. È utilissimo
    # per riferirci a questa pagina nel resto del codice senza scrivere l'URL per esteso.
    path('login/', CustomLoginView.as_view(), name='login'),
    
    # NUOVO URL per il logout
    # Quando un utente visita '/accounts/logout/', Django esegue la LogoutView.
    # Questa vista lo slogga e poi lo reindirizza a LOGOUT_REDIRECT_URL
    # che abbiamo definito in settings.py.
    path('logout/', LogoutView.as_view(), name='logout'),
]