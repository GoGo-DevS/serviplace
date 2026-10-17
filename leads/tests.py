"""Medición del embudo (18-10-2026).

Lo que se protege: que los números del panel signifiquen lo que dicen. Un bot
contado como visita, un teléfono guardado en una búsqueda o un panel abierto
a cualquiera son peores que no medir.
"""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from core.antispam import HONEYPOT_FIELD, TIMESTAMP_FIELD
from directory.models import Category, Commune, Provider, Region
from directory.tests_profesionales import sello_humano

from .models import LeadEvent

User = get_user_model()
HUMANO = {'HTTP_USER_AGENT': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/604.1'}
GOOGLE = {'HTTP_USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
WHATSAPP = {'HTTP_USER_AGENT': 'WhatsApp/2.23.20.0 A'}


class Base(TestCase):
    def setUp(self):
        region = Region.objects.create(name='RM', slug='rm', is_active=True)
        self.maipu = Commune.objects.create(region=region, name='Maipú', slug='maipu', is_active=True)
        call_command('seed_categorias', stdout=StringIO())
        self.gasfiter = Category.objects.get(slug='gasfiteria')
        dueno = User.objects.create_user('dueno-de-prueba', password='clave-larga-de-verdad-99')
        self.perfil = Provider.objects.create(owner=dueno, 
            business_name='Gásfiter Uno', contact_name='Juan', category=self.gasfiter, commune=self.maipu,
            sector='Centro', description='Descripción.', short_description='Corta.',
            phone='+56 9 1111 2222', whatsapp_number='56911112222', is_active=True)


class LosBotsNoCuentan(Base):

    def test_una_persona_suma_una_vista_y_un_evento(self):
        self.client.get(self.perfil.get_absolute_url(), **HUMANO)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.views_count, 1)
        self.assertEqual(LeadEvent.objects.filter(event_type=LeadEvent.DETAIL_VIEW).count(), 1)

    def test_google_y_la_vista_previa_de_whatsapp_no_suman(self):
        """Compartir un perfil por WhatsApp hace que WhatsApp lo descargue para
        la vista previa: eso no es una persona mirando."""
        self.client.get(self.perfil.get_absolute_url(), **GOOGLE)
        self.client.get(self.perfil.get_absolute_url(), **WHATSAPP)
        self.client.get(reverse('directory:whatsapp_redirect', args=[self.perfil.slug]), **GOOGLE)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.views_count, 0)
        self.assertEqual(self.perfil.whatsapp_clicks_count, 0)
        self.assertFalse(LeadEvent.objects.exists())

    def test_el_bot_igual_ve_la_pagina(self):
        """Excluirlo de la medición no puede excluirlo del sitio: Google tiene que indexar."""
        r = self.client.get(self.perfil.get_absolute_url(), **GOOGLE)
        self.assertEqual(r.status_code, 200)


class Busquedas(Base):

    def test_una_busqueda_sin_resultados_queda_registrada_con_su_contexto(self):
        self.client.get(reverse('directory:provider_list') + '?categoria=kinesiologia&comuna=maipu', **HUMANO)
        e = LeadEvent.objects.get(event_type=LeadEvent.SEARCH)
        self.assertEqual((e.category_slug, e.commune_slug, e.results_count), ('kinesiologia', 'maipu', 0))

    def test_cuenta_los_resultados_reales(self):
        self.client.get(reverse('directory:provider_list') + '?categoria=gasfiteria', **HUMANO)
        self.assertEqual(LeadEvent.objects.get(event_type=LeadEvent.SEARCH).results_count, 1)

    def test_no_guarda_un_telefono_escrito_en_el_buscador(self):
        self.client.get(reverse('directory:provider_list') + '?q=gasfiter+llamar+al+9+8765+4321', **HUMANO)
        q = LeadEvent.objects.get(event_type=LeadEvent.SEARCH).query
        self.assertNotIn('8765', q)
        self.assertIn('gasfiter', q)

    def test_cambiar_de_pagina_no_es_otra_busqueda(self):
        self.client.get(reverse('directory:provider_list') + '?categoria=gasfiteria&page=2', **HUMANO)
        self.assertFalse(LeadEvent.objects.filter(event_type=LeadEvent.SEARCH).exists())

    def test_no_se_guarda_ni_ip_ni_agente(self):
        self.client.get(reverse('directory:provider_list') + '?q=gasfiter', REMOTE_ADDR='200.1.2.3', **HUMANO)
        e = LeadEvent.objects.get()
        valores = ' '.join(str(getattr(e, f.name)) for f in LeadEvent._meta.fields)
        self.assertNotIn('200.1.2.3', valores)
        self.assertNotIn('iPhone', valores)
        self.assertEqual(len(e.visitor), 16)


class EmbudoDelProfesional(Base):

    def test_registro_iniciado_cuenta_creada_y_perfil_publicado(self):
        self.client.get(reverse('accounts:register'), **HUMANO)
        self.client.post(reverse('accounts:register'), {
            'username': 'camila', 'email': 'c@example.cl',
            'password1': 'clave-larga-de-verdad-99', 'password2': 'clave-larga-de-verdad-99',
            TIMESTAMP_FIELD: sello_humano(), HONEYPOT_FIELD: '',
        }, **HUMANO)
        self.client.post(reverse('accounts:provider_create'), {
            'business_name': 'Gasfitería Camila', 'contact_name': 'Camila', 'category': self.gasfiter.pk,
            'commune': self.maipu.pk, 'sector': 'Centro', 'short_description': 'Gásfiter en Maipú.',
            'description': 'Atiendo filtraciones y calefont en todo Maipú.', 'phone': '+56 9 8765 4321',
            'whatsapp_number': '+56 9 8765 4321', 'attends_home': 'on',
            TIMESTAMP_FIELD: sello_humano(), HONEYPOT_FIELD: '',
        }, **HUMANO)
        tipos = set(LeadEvent.objects.values_list('event_type', flat=True))
        esperados = {LeadEvent.SIGNUP_STARTED, LeadEvent.SIGNUP_DONE, LeadEvent.PROFILE_PUBLISHED}
        self.assertTrue(esperados <= tipos, tipos)


class PanelDeMetricas(Base):

    def test_un_usuario_comun_no_lo_ve(self):
        u = User.objects.create_user('comun', password='clave-larga-de-verdad-99')
        self.client.force_login(u)
        self.assertEqual(self.client.get(reverse('core:metricas')).status_code, 404)

    def test_sin_sesion_pide_entrar(self):
        self.assertEqual(self.client.get(reverse('core:metricas')).status_code, 302)

    def test_el_staff_ve_el_embudo_y_las_busquedas_sin_resultados(self):
        self.client.get(reverse('directory:provider_list') + '?categoria=kinesiologia&comuna=maipu', **HUMANO)
        self.client.get(self.perfil.get_absolute_url(), **HUMANO)
        staff = User.objects.create_user('staff', password='clave-larga-de-verdad-99', is_staff=True)
        self.client.force_login(staff)
        r = self.client.get(reverse('core:metricas'))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn('Búsquedas sin resultados', html)
        self.assertIn('Kinesiología', html)
        self.assertEqual(r.context['busquedas'], 1)
        self.assertEqual(r.context['sin_resultados'], 1)
        self.assertEqual(r.context['vistas'], 1)
        self.assertEqual(r.context['diagnostico'][0], 'E', 'con 1 visitante no hay conclusiones')

    def test_el_panel_no_hace_una_consulta_por_evento(self):
        staff = User.objects.create_user('staff', password='clave-larga-de-verdad-99', is_staff=True)
        self.client.force_login(staff)
        self.client.get(reverse('core:metricas'))
        with self.assertNumQueries(18) as pocos:
            self.client.get(reverse('core:metricas'))
        # Leído YA: cada petición siguiente limpia el registro de consultas.
        base = len(pocos.captured_queries)
        for _ in range(40):
            self.client.get(self.perfil.get_absolute_url(), **HUMANO)
            self.client.get(reverse('directory:provider_list') + '?q=x', **HUMANO)
        with self.assertNumQueries(base):
            self.client.get(reverse('core:metricas'))
