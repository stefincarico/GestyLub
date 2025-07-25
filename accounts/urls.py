# accounts/urls.py

from django.urls import path
from .views import CustomLoginView

# Questo è l'elenco degli URL specifici per questa app.
urlpatterns = [
    # Quando l'URL è 'login/', esegui la vista CustomLoginView.
    # 'as_view()' è necessario perché stiamo usando una vista basata su classi.
    # 'name="login"' assegna un nome univoco a questo URL. È utilissimo
    # per riferirci a questa pagina nel resto del codice senza scrivere l'URL per esteso.
    path('login/', CustomLoginView.as_view(), name='login'),
]