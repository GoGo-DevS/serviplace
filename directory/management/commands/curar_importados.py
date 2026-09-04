"""
Cura lo que trae Google Maps antes de que lo vea un vecino. Determinista, sin IA.

Lo que Google devuelve para "Jardinería Puente Alto" incluye jardines INFANTILES;
para "Pintura" trae academias de arte y desabolladurías; y una búsqueda por comuna
trae negocios de la comuna de al lado (o de Buenos Aires). Este comando:

  1. Normaliza teléfonos al formato +56 9 XXXX XXXX y deja WhatsApp solo en móviles.
  2. Reasigna la comuna leyendo la dirección (el negocio ESTÁ donde dice su dirección).
  3. Oculta lo que no es un servicio a domicilio (jardín infantil, academia, taller
     automotriz salvo cerrajería, centro comercial...) y lo que está fuera de Chile.
  4. Oculta duplicados por teléfono (mismo negocio importado en dos comunas).

NADA SE BORRA: se oculta con is_active=False + moderation_note, reversible desde el
panel de moderación. Dry-run por defecto; escribe con --confirmar. Idempotente.
"""
import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from directory.models import Commune, Provider

TIPOS_BLOQUEADOS = {
    'Institución educativa', 'Centro comercial', 'Tienda de alimentación',
    'Servicio de lavado de coches', 'Centro cultural', 'Granja', 'Escuela',
    'Colegio', 'Jardín de infancia', 'Guardería', 'Universidad', 'Museo', 'Restaurante',
}
TIPOS_AUTOMOTRIZ = {'Taller de automóviles', 'Concesionario de automóviles', 'Taller de carrocería'}
NOMBRE_BLOQUEADO = re.compile(
    r'jard[ií]n\s+infantil|sala\s+cuna|jard[ií]n\s+de\s+(la|el|los|las)\b|academia|clases\s+de|'
    r'corporaci[oó]n\s+cultural|desabolladura|detailing|lavado\s+de\s+autos|manualidades|'
    r'homecenter|sodimac|\beasy\b|pizarre[ñn]o|colegio|escuela|liceo|universidad|'
    r'tienda\s+online|supermercado|farmacia|\bbanco\b',
    re.IGNORECASE,
)
AUTOMOTRIZ = re.compile(r'automotr?iz|automotive|vehicul', re.IGNORECASE)
MARCA_CHILE = re.compile(r'Regi[oó]n|Chile|Santiago', re.IGNORECASE)


def normalizar_telefono(raw):
    """Devuelve (phone_bonito, whatsapp_digits). WhatsApp solo si es móvil chileno."""
    digitos = ''.join(ch for ch in (raw or '') if ch.isdigit())
    if digitos.startswith('56') and len(digitos) == 11:
        pass
    elif len(digitos) == 9 and digitos[0] in '92':
        digitos = '56' + digitos
    elif len(digitos) == 8:
        digitos = '562' + digitos
    else:
        return (raw or '').strip(), ''
    if digitos.startswith('569'):
        return f'+56 9 {digitos[3:7]} {digitos[7:]}', digitos
    if digitos.startswith('562'):
        return f'+56 2 {digitos[3:7]} {digitos[7:]}', ''
    return (raw or '').strip(), ''


def comuna_en_direccion(direccion, comunas_por_nombre):
    """
    La comuna es el SEGMENTO de localidad de la dirección de Google ("Calle 123, 8150215 Puente
    Alto, Región Metropolitana"), no cualquier aparición del nombre: "Av. Bernardo O'Higgins"
    no es la comuna de O'Higgins. Se toma el último segmento que sea exactamente una comuna.
    """
    if not direccion:
        return None
    candidatos = []
    for seg in direccion.split(','):
        limpio = re.sub(r'^[\s\d]+', '', seg).strip()
        if limpio in comunas_por_nombre:
            candidatos.append(comunas_por_nombre[limpio])
    return candidatos[-1] if candidatos else None


def tipo_de(p):
    return p.source_notes.split('Tipo: ')[-1].strip() if 'Tipo: ' in p.source_notes else ''


class Command(BaseCommand):
    help = 'Normaliza, reubica y oculta importados de Google Maps que no son servicios. Dry-run por defecto.'

    def add_arguments(self, parser):
        parser.add_argument('--confirmar', action='store_true')

    def handle(self, *args, **opts):
        for stream in (self.stdout, self.stderr):
            try:
                stream._out.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
        confirmar = opts['confirmar']
        # "Santiago" es comuna y también aparece en direcciones de toda la RM: se excluye del match.
        comunas = {c.name: c for c in Commune.objects.filter(is_active=True) if c.name != 'Santiago'}
        qs = list(Provider.objects.filter(source_name='Google Maps', owner__isnull=True).select_related('commune', 'category'))

        cambios = {'telefono': 0, 'comuna': 0, 'oculto_tipo': 0, 'oculto_pais': 0, 'oculto_dup': 0}
        hoy = timezone.now()
        vistos_por_tel = {}

        with transaction.atomic():
            for p in qs:
                # 1. teléfono
                bonito, wa = normalizar_telefono(p.phone)
                if bonito != p.phone or wa != p.whatsapp_number:
                    cambios['telefono'] += 1
                    p.phone, p.whatsapp_number = bonito, wa

                # 2. comuna según dirección
                real = comuna_en_direccion(p.address, comunas)
                if real and real.pk != p.commune_id:
                    cambios['comuna'] += 1
                    p.source_notes += f' | Comuna reasignada: {p.commune.name} → {real.name} (según dirección)'
                    p.commune = real
                    p.service_area = f'{real.name} y alrededores'
                    p.sector = p.address[:120] if p.address else real.name

                # 3. no es un servicio / fuera de Chile
                motivo = ''
                tipo = tipo_de(p)
                if p.address and not MARCA_CHILE.search(p.address):
                    motivo = f'Fuera de Chile: {p.address[-60:]}'
                    cambios['oculto_pais'] += 1
                elif tipo in TIPOS_BLOQUEADOS or NOMBRE_BLOQUEADO.search(p.business_name):
                    motivo = f'No es un servicio a domicilio (tipo Google: {tipo or "sin tipo"})'
                    cambios['oculto_tipo'] += 1
                elif p.category.slug != 'cerrajeria' and (tipo in TIPOS_AUTOMOTRIZ or AUTOMOTRIZ.search(p.business_name)):
                    motivo = f'Rubro automotriz, no {p.category.name} a domicilio'
                    cambios['oculto_tipo'] += 1

                # 4. duplicado por teléfono
                if not motivo and p.whatsapp_number:
                    previo = vistos_por_tel.get(p.whatsapp_number)
                    if previo is not None:
                        motivo = f'Duplicado de #{previo.pk} ({previo.business_name}), mismo teléfono'
                        cambios['oculto_dup'] += 1
                    else:
                        vistos_por_tel[p.whatsapp_number] = p

                if motivo and p.is_active:
                    p.is_active = False
                    p.hidden_at = hoy
                    p.moderation_note = f'[curar_importados] {motivo}'
                    self.stdout.write(f'  ocultar #{p.pk} {p.business_name[:45]:45s} → {motivo}')

                if confirmar:
                    p.save()

            if not confirmar:
                transaction.set_rollback(True)

        activos = Provider.objects.filter(is_active=True).count()
        self.stdout.write(
            f'\nTeléfonos normalizados: {cambios["telefono"]} | Comuna reasignada: {cambios["comuna"]} | '
            f'Ocultos: tipo {cambios["oculto_tipo"]}, país {cambios["oculto_pais"]}, duplicado {cambios["oculto_dup"]}'
        )
        if confirmar:
            self.stdout.write(self.style.SUCCESS(f'Escrito. Activos ahora: {activos}'))
        else:
            self.stdout.write(self.style.WARNING('[DRY-RUN] Nada escrito. Agrega --confirmar.'))
