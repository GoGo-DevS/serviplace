"""Código de confirmación de WhatsApp para los perfiles que ya existían (30-10-2026)."""
import secrets

from django.db import migrations


def llenar(apps, schema_editor):
    Provider = apps.get_model('directory', 'Provider')
    for p in Provider.objects.filter(whatsapp_codigo='').only('pk'):
        Provider.objects.filter(pk=p.pk).update(whatsapp_codigo=f'SP-{secrets.randbelow(9000) + 1000}')


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0018_sellos'),
    ]

    operations = [
        migrations.RunPython(llenar, migrations.RunPython.noop),
    ]
