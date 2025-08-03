# gestionale/migrations/00XX_add_tenant_id_to_dipendentedettaglio.py

from django.db import migrations
from django.db.models import ForeignKey
import django.db.models.deletion
from tenants.models import Company


class Migration(migrations.Migration):

    dependencies = [
        ('gestionale', '0002_add_tenant_id_to_documentoriga'),  # Assicurati che questo sia il nome della migrazione precedente
    ]

    operations = [
        migrations.AddField(
            model_name='dipendentedettaglio',
            name='tenant',
            field=ForeignKey(
                default=1,  # Sostituisci con l'ID del tuo tenant predefinito
                on_delete=django.db.models.deletion.CASCADE,
                related_name='gestionale_dipendentedettaglio_related',
                to='tenants.company',
            ),
            preserve_default=False,
        ),
    ]