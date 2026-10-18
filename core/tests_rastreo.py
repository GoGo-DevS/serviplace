"""Rastreo completo del sitio, como Screaming Frog (18-10-2026).

La auditoría de Jorge a medina4x4 encontró títulos duplicados, metas vacías
y H1 múltiples en el 90% de las páginas: cosas que ninguna prueba unitaria ve
porque cada una mira una página. Esta recorre TODO lo público (portada,
sitemap y cada enlace interno que encuentra) con perfiles reales sembrados.
"""
import html
import json
import re
from collections import Counter, deque
from io import StringIO
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from directory.models import Category, Commune, Provider, Region

User = get_user_model()
SITE = 'https://serviplace.cl'
NO_RASTREAR = ('/cuenta/', '/admin/', '/static/', '/media/')


@override_settings(SITE_URL=SITE)
class RastreoCompleto(TestCase):

    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(name='Región Metropolitana', slug='rm', is_active=True)
        maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        cerrillos = Commune.objects.create(region=region, name='Cerrillos', slug='cerrillos', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        for i, (cat, comuna, extra) in enumerate([
            ('kinesiologia', maipu, dict(profession_title='Kinesióloga', institution='Universidad de Chile',
                                         graduation_year=2019, health_registry='654321', attends_home=True)),
            ('gasfiteria', maipu, {}),
            ('gasfiteria', cerrillos, {}),
            ('clases-particulares', cerrillos, dict(profession_title='Profesor de matemáticas')),
            ('repuestos-automotrices', maipu, dict(website='https://repuestos.example.cl', instagram='repuestos')),
        ]):
            dueno = User.objects.create_user(f'dueno{i}', password='clave-larga-de-verdad-99')
            Provider.objects.create(
                business_name=f'Perfil {i} {cat}', contact_name=f'Persona {i}', owner=dueno,
                category=Category.objects.get(slug=cat), commune=comuna, sector='Centro',
                description='Descripción del servicio con detalle suficiente.', short_description=f'Resumen {i}.',
                phone='+56 9 1111 2222', whatsapp_number='56911112222', is_active=True, **extra)

    def rastrear(self):
        pendientes = deque(['/'])
        sitemap = self.client.get('/sitemap.xml').content.decode()
        pendientes.extend(urlsplit(loc).path for loc in re.findall(r'<loc>(.*?)</loc>', sitemap))
        paginas, origen = {}, {}
        while pendientes and len(paginas) < 400:
            ruta = pendientes.popleft()
            if ruta in paginas or ruta.startswith(NO_RASTREAR) or ruta.endswith('/whatsapp/'):
                continue
            respuesta = self.client.get(ruta)
            paginas[ruta] = respuesta
            if respuesta.status_code != 200 or 'text/html' not in respuesta['Content-Type']:
                continue
            texto = respuesta.content.decode()
            for href in re.findall(r'href="(/[^"#?]*)', texto):
                if href not in paginas:
                    origen.setdefault(href, ruta)
                    pendientes.append(href)
        return paginas, origen

    def test_todo_lo_publico_cumple_el_checklist_de_seo(self):
        paginas, origen = self.rastrear()
        self.assertGreater(len(paginas), 60, 'el rastreo debería recorrer decenas de páginas')
        rotas = {r: (p.status_code, origen.get(r)) for r, p in paginas.items() if p.status_code >= 400}
        self.maxDiff = None
        self.assertEqual(rotas, {}, 'enlaces internos rotos (ruta: estado, desde)')

        titulos, metas = Counter(), Counter()
        for ruta, respuesta in paginas.items():
            if respuesta.status_code != 200 or 'text/html' not in respuesta['Content-Type']:
                continue
            texto = respuesta.content.decode()
            robots = re.search(r'<meta name="robots" content="([^"]*)"', texto)
            indexable = not (robots and 'noindex' in robots.group(1))
            self.assertEqual(texto.count('<title>'), 1, ruta)
            self.assertEqual(len(re.findall(r'<h1[ >]', texto)), 1, f'{ruta}: debe tener un solo h1')
            for bloque in re.findall(r'<script type="application/ld\+json">(.*?)</script>', texto, re.S):
                json.loads(bloque)  # un bloque mal formado Google lo descarta entero sin avisar
            if not indexable:
                continue
            titulo = html.unescape(re.search(r'<title>(.*?)</title>', texto, re.S).group(1).strip())
            meta = re.search(r'<meta name="description" content="([^"]*)"', texto)
            self.assertTrue(meta and len(meta.group(1)) >= 50, f'{ruta}: sin meta description útil')
            titulos[titulo] += 1
            metas[meta.group(1)] += 1
            canonical = re.search(r'<link rel="canonical" href="([^"]*)"', texto).group(1)
            self.assertTrue(canonical.startswith(SITE), f'{ruta}: canonical no absoluto ({canonical})')
            self.assertEqual(urlsplit(canonical).path, ruta, f'{ruta}: canonical apunta a otra página')
        self.assertEqual([t for t, n in titulos.items() if n > 1], [], 'títulos duplicados')
        self.assertEqual([m for m, n in metas.items() if n > 1], [], 'meta descriptions duplicadas')

    def test_el_sitemap_solo_publica_paginas_indexables(self):
        sitemap = self.client.get('/sitemap.xml').content.decode()
        for loc in re.findall(r'<loc>(.*?)</loc>', sitemap):
            ruta = urlsplit(loc).path
            respuesta = self.client.get(ruta)
            self.assertEqual(respuesta.status_code, 200, ruta)
            robots = re.search(r'<meta name="robots" content="([^"]*)"', respuesta.content.decode())
            self.assertFalse(robots and 'noindex' in robots.group(1), f'{ruta} está en el sitemap y es noindex')
