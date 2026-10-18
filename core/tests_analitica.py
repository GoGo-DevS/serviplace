"""GA4 (18-10-2026), con el criterio de los demás sitios de GoGoDevS
(memoria analitica-ga4-por-sitio): vacío no carga nada, lo privado no se mide,
y el clic de WhatsApp se llama como lo cuenta el reporte semanal del CRM.
"""
import time
from io import StringIO

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, Region

User = get_user_model()
GA = 'G-PRUEBA123'


class Base(TestCase):
    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.cat = Category.objects.get(slug='gasfiteria')
        self.dueno = User.objects.create_user('dueno', password='clave-larga-de-verdad-99')
        self.perfil = Provider.objects.create(
            business_name='Gasfitería Uno', contact_name='Ana', category=self.cat, commune=self.maipu,
            sector='Centro', description='Descripción del servicio.', short_description='Resumen.',
            phone='+56 9 1111 2222', whatsapp_number='56911112222', is_active=True, owner=self.dueno)


class SinIdentificadorNoSeCargaNada(Base):

    @override_settings(GA4_MEASUREMENT_ID='')
    def test_vacio_no_hay_ni_script_ni_peticion_a_google(self):
        self.assertNotIn('googletagmanager', self.client.get('/').content.decode())


@override_settings(GA4_MEASUREMENT_ID=GA)
class ConIdentificador(Base):

    def test_las_paginas_publicas_se_miden(self):
        for url in ('/', '/profesionales/', self.perfil.get_absolute_url(), reverse('accounts:register')):
            self.assertIn(f'gtag/js?id={GA}', self.client.get(url).content.decode(), url)

    def test_lo_privado_no_se_manda_a_google(self):
        """Panel, métricas y edición del perfil: datos que no son de Google."""
        self.client.force_login(self.dueno)
        for url in (reverse('accounts:dashboard'),
                    reverse('accounts:provider_edit', args=[self.perfil.slug])):
            self.assertNotIn('googletagmanager', self.client.get(url).content.decode(), url)
        staff = User.objects.create_user('staff', password='clave-larga-de-verdad-99', is_staff=True)
        self.client.force_login(staff)
        self.assertNotIn('googletagmanager', self.client.get(reverse('core:metricas')).content.decode())

    def test_las_visitas_del_staff_no_son_trafico(self):
        staff = User.objects.create_user('staff', password='clave-larga-de-verdad-99', is_staff=True)
        self.client.force_login(staff)
        self.assertNotIn('googletagmanager', self.client.get('/').content.decode())

    def test_el_whatsapp_se_informa_como_contacto_whatsapp(self):
        """Es el nombre que el reporte semanal del CRM cuenta como contacto."""
        html = self.client.get(self.perfil.get_absolute_url()).content.decode()
        self.assertIn('data-ga="contacto_whatsapp"', html)
        html = self.client.get('/servicios/gasfiteria/maipu/').content.decode()
        self.assertIn('data-ga="contacto_whatsapp"', html)

    def test_una_busqueda_se_informa_con_su_termino(self):
        html = self.client.get('/servicios/?q=gasfiter').content.decode()
        self.assertIn('"search_term": "gasfiter"', html)
        self.assertIn("gtag('event', 'search'", html)

    def test_registrarse_se_informa_una_sola_vez(self):
        self.client.post(reverse('accounts:register'), {
            'username': 'nueva', 'email': 'n@example.cl',
            'password1': 'clave-larga-de-verdad-99', 'password2': 'clave-larga-de-verdad-99',
            TIMESTAMP_FIELD: signing.dumps(int(time.time()) - 60, salt='antispam'), HONEYPOT_FIELD: '',
        })
        primera = self.client.get(reverse('accounts:provider_create')).content.decode()
        segunda = self.client.get(reverse('accounts:provider_create')).content.decode()
        self.assertIn("gtag('event', 'sign_up')", primera)
        self.assertNotIn("gtag('event', 'sign_up')", segunda, 'un registro contado dos veces')
