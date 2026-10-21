"""Repara las tildes corridas que dejó el lector de CV (20-10-2026).

Un perfil quedó publicado como "Ingeniero Inforḿatico": el PDF (LaTeX) traía
la tilde antes de la vocal y quedó pegada a la consonante. El lector ya está
arreglado (accounts.cv.reparar_tildes); esto corrige lo que ya se guardó.

Solo título e institución (los campos que llena el CV) y solo el patrón que en
español no existe: consonante con tilde aguda seguida de vocal, vocal con
virgulilla seguida de n, g con diéresis seguida de u. La lógica va copiada:
una migración no puede depender de código que después cambie.
"""
import re
import unicodedata

from django.db import migrations


def _reparar(texto):
    nfd = unicodedata.normalize('NFD', texto)
    nfd = re.sub(r'([^\W\d_aeiouAEIOU])\u0301([aeiouAEIOU])', lambda m: m.group(1) + m.group(2) + '\u0301', nfd)
    nfd = re.sub(r'([aeiouAEIOU])\u0303([nN])', lambda m: m.group(1) + m.group(2) + '\u0303', nfd)
    nfd = re.sub(r'([gG])\u0308([uU])', lambda m: m.group(1) + m.group(2) + '\u0308', nfd)
    return unicodedata.normalize('NFC', nfd)


def reparar(apps, schema_editor):
    Provider = apps.get_model('directory', 'Provider')
    for p in Provider.objects.exclude(profession_title='', institution='').only('pk', 'profession_title', 'institution'):
        cambios = {}
        for campo in ('profession_title', 'institution'):
            valor = getattr(p, campo) or ''
            nuevo = _reparar(valor)
            if nuevo != unicodedata.normalize('NFC', valor):
                cambios[campo] = nuevo
        if cambios:
            Provider.objects.filter(pk=p.pk).update(**cambios)


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0016_otros_rubros'),
    ]

    operations = [
        migrations.RunPython(reparar, migrations.RunPython.noop),
    ]
