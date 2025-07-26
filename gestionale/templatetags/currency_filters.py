# gestionale/templatetags/currency_filters.py

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from decimal import Decimal

register = template.Library()

@register.filter(name='format_currency')
def format_currency(value):
    """
    Filtro per formattare un valore numerico come valuta italiana (es. 12345.67 -> "12.345,67").
    Gestisce correttamente Decimal, float e int.
    """
    if value is None:
        return ""
        
    try:
        # 1. Assicuriamoci che sia un Decimal per l'arrotondamento corretto
        val_decimal = Decimal(value).quantize(Decimal('0.01'))
        
        # 2. Dividiamo la parte intera da quella decimale
        parte_intera, parte_decimale = str(val_decimal).split('.')
        
        # 3. Applichiamo il separatore delle migliaia solo alla parte intera
        parte_intera_formattata = intcomma(parte_intera)
        
        # 4. Ricomponiamo la stringa con la virgola come separatore decimale
        return f"{parte_intera_formattata},{parte_decimale}"
        
    except (ValueError, TypeError):
        # Se il valore non è un numero, restituiscilo così com'è
        return value
    

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Tag per sostituire o aggiungere parametri GET all'URL corrente.
    Esempio di uso: {% url_replace page=3 %}
    """
    # Crea una copia modificabile dei parametri GET attuali
    query = context['request'].GET.copy()
    
    # Itera sugli argomenti passati al tag (es. page=3, order_by='name')
    for key, value in kwargs.items():
        # Aggiorna o aggiunge il parametro nella nostra copia
        query[key] = value
        
    # Restituisce i parametri codificati come stringa per l'URL
    return query.urlencode()