from django.core.management.base import BaseCommand
from django.utils.text import slugify

from directory.models import Category, Commune, Provider


AUTHORIZED_PROVIDERS = [
    {
        'business_name': 'Cerrajero Vega Maipú',
        'contact_name': 'Cerrajero Vega',
        'category': 'Cerrajería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Cerrajería profesional a domicilio en Maipú.',
        'description': 'Servicio de cerrajería a domicilio para apertura de puertas, autos, cambio de cerraduras y urgencias. Información pública revisada y autorización obtenida por Diego para aparecer en SERVIPLACE Maipú.',
        'phone': '+56992391520',
        'whatsapp_number': '56992391520',
        'service_area': 'Maipú y Región Metropolitana',
        'source_name': 'Cerrajero Vega',
        'source_url': 'https://cerrajerovega.cl/cerrajero-en-maipu',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'Alo Cerrajero Maipú',
        'contact_name': 'Alo Cerrajero',
        'category': 'Cerrajería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Cerrajero a domicilio en Maipú.',
        'description': 'Servicio de cerrajería a domicilio, apertura de puertas, cambios de chapas y urgencias. Información pública revisada y autorización obtenida por Diego para aparecer en SERVIPLACE Maipú.',
        'phone': '+56950195849',
        'whatsapp_number': '56950195849',
        'service_area': 'Maipú',
        'source_name': 'Alo Cerrajero',
        'source_url': 'https://www.alocerrajero.cl/maipu.html',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'Cerrajería Ibáñez Maipú',
        'contact_name': 'Cerrajería Ibáñez',
        'category': 'Cerrajería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Cerrajería 24/7 con cobertura en Maipú.',
        'description': 'Servicio de cerrajería 24/7, apertura de puertas, cambio de cerraduras, cerrajería automotriz y atención de urgencias. Información pública revisada y autorización obtenida por Diego.',
        'phone': '+56989758412',
        'whatsapp_number': '56989758412',
        'service_area': 'Maipú y Región Metropolitana',
        'source_name': 'Cerrajería Ibáñez',
        'source_url': 'https://cerrajeroibanez.cl/cerrajero-en-maipu/',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'Grifería Carola',
        'contact_name': 'Grifería Carola',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Gasfitería y grifería local en Maipú.',
        'description': 'Servicio/local de grifería y gasfitería en Maipú. Información pública revisada y autorización obtenida por Diego para aparecer en SERVIPLACE Maipú.',
        'phone': '+56989920770',
        'whatsapp_number': '56989920770',
        'service_area': 'Maipú',
        'source_name': 'Grifería Carola',
        'source_url': 'https://griferiacarola.cl/',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'Cumbre Partner Gasfiter Maipú',
        'contact_name': 'Cumbre Partner',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Gasfiter a domicilio en Maipú.',
        'description': 'Servicio de gasfitería a domicilio para reparaciones, destapes, filtraciones, calefont, cañerías e instalaciones. Información pública revisada y autorización obtenida por Diego.',
        'phone': '+56962234483',
        'whatsapp_number': '56962234483',
        'service_area': 'Maipú',
        'source_name': 'Cumbre Partner',
        'source_url': 'https://www.cumbrepartner.com/gasfiter-maipu/',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'Plomero.cl Maipú',
        'contact_name': 'Plomero.cl',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Gasfitería profesional a domicilio en Maipú.',
        'description': 'Servicio de gasfitería para urgencias, fugas, rebalses, filtraciones y mantenciones. Información pública revisada y autorización obtenida por Diego.',
        'phone': '+56961913434',
        'whatsapp_number': '56961913434',
        'service_area': 'Maipú y Gran Santiago',
        'source_name': 'Plomero.cl',
        'source_url': 'https://plomero.cl/comunas/gasfiter-en-maipu/',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'Soluciones Eléctricas CL Maipú',
        'contact_name': 'Soluciones Eléctricas CL',
        'category': 'Electricidad',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Electricista a domicilio en Maipú.',
        'description': 'Servicios eléctricos, emergencias, revisiones, mantenciones, tableros, enchufes, iluminación y trabajos eléctricos en Maipú. Información pública revisada y autorización obtenida por Diego.',
        'phone': '+56972361592',
        'whatsapp_number': '56972361592',
        'service_area': 'Maipú y Región Metropolitana',
        'source_name': 'Soluciones Eléctricas CL',
        'source_url': 'https://solucionelectricas.cl/electricista-en-maipu/',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'MegaClima Maipú',
        'contact_name': 'MegaClima',
        'category': 'Climatización',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Mantención e instalación de aire acondicionado en Maipú.',
        'description': 'Servicio de climatización, mantención preventiva, instalación y revisión de aire acondicionado en Maipú. Información pública revisada y autorización obtenida por Diego.',
        'phone': '+56923977662',
        'whatsapp_number': '56923977662',
        'service_area': 'Maipú',
        'source_name': 'MegaClima',
        'source_url': 'https://www.megaclima.cl/mantencion-de-aire-acondicionado-en-maipu',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'José Maestro Sureño',
        'contact_name': 'José Maestro Sureño',
        'category': 'Construcción',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Maestro constructor en Maipú.',
        'description': 'Servicios de construcción, remodelación, ampliaciones, cerámicas, electricidad, gasfitería, cobertizos, estructuras metálicas y pintura. Información pública revisada y autorización obtenida por Diego.',
        'phone': '+56998601170',
        'whatsapp_number': '56998601170',
        'service_area': 'Maipú y Santiago',
        'source_name': 'Perfil Comercial',
        'source_url': 'https://perfilcomercial.cl/listing/electrico-ampliaciones-gasfiter-maipu/',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'Construcciones y Remodelaciones',
        'contact_name': 'Construcciones y Remodelaciones',
        'category': 'Construcción',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Construcciones y remodelaciones en Maipú.',
        'description': 'Servicio de construcciones, remodelaciones, ampliaciones y trabajos generales. Información pública revisada y autorización obtenida por Diego.',
        'phone': '+56968453133',
        'whatsapp_number': '56968453133',
        'service_area': 'Maipú',
        'source_name': 'Maipú a su Servicio',
        'source_url': 'https://maipuasuservicio.cl/construcciones-y-remodelaciones/',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'Renovación de Propiedades',
        'contact_name': 'Renovación de Propiedades',
        'category': 'Limpieza',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Renovación, pintura y limpieza de alfombras.',
        'description': 'Servicios de renovación de propiedades, papel mural, pisos, pintura y limpieza de alfombras. Información pública revisada y autorización obtenida por Diego.',
        'phone': '+56936585846',
        'whatsapp_number': '56936585846',
        'service_area': 'Maipú',
        'source_name': 'Maipú a su Servicio',
        'source_url': 'https://maipuasuservicio.cl/renovacion-de-propiedades/',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
    {
        'business_name': 'Jardinería Maipú',
        'contact_name': 'Jardinería Maipú',
        'category': 'Jardinería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Mantención de jardines y áreas verdes.',
        'description': 'Servicio de jardinería, mantención de áreas verdes y fumigación. Información pública revisada y autorización obtenida por Diego.',
        'phone': '+56951597516',
        'whatsapp_number': '56951597516',
        'service_area': 'Maipú',
        'source_name': 'Jardinería Maipú',
        'source_url': 'https://www.facebook.com/jardineriamaipu/',
        'source_notes': 'Prestador contactado por Diego. Autorizó aparecer en SERVIPLACE Maipú.',
    },
]


NEW_PUBLIC_PROSPECTS = [
    {
        'business_name': 'TodoGasfiter Maipú',
        'contact_name': 'TodoGasfiter',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Gasfitería a domicilio en Maipú.',
        'description': 'Servicio de gasfitería a domicilio, destapes de alcantarillado, filtraciones, reparación de cañerías, WC, lavaplatos, calefont, obras civiles, ampliaciones y remodelaciones. Dato público encontrado para revisión y contacto.',
        'phone': '+56992084378',
        'whatsapp_number': '56992084378',
        'service_area': 'Maipú y Región Metropolitana',
        'source_name': 'TodoGasfiter',
        'source_url': 'https://www.todogasfiter.cl/gasfiter-en-maipu.html',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Electricista24 Maipú',
        'contact_name': 'Electricista24',
        'category': 'Electricidad',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Electricista a domicilio 24 horas en Maipú.',
        'description': 'Servicios eléctricos, urgencias 24 horas, técnicos eléctricos, reparaciones, tableros, enchufes, iluminación, citofonía y mantención eléctrica. Dato público encontrado para revisión y contacto.',
        'phone': '+56972412050',
        'whatsapp_number': '56972412050',
        'service_area': 'Maipú',
        'source_name': 'Electricista24',
        'source_url': 'https://electricista24.cl/electricista-en-maipu.html',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Aquí Gásfiter Maipú',
        'contact_name': 'Aquí Gásfiter',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Servicio de gásfiter en Maipú.',
        'description': 'Servicio de gásfitería con equipo humano calificado, soluciones confiables y múltiples canales de contacto. Dato público encontrado para revisión y contacto.',
        'phone': '+56921778479',
        'whatsapp_number': '56921778479',
        'service_area': 'Maipú',
        'source_name': 'Aquí Gásfiter',
        'source_url': 'https://www.aquigasfiter.cl/maipu.html',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Lavado de Alfombras Chile Maipú',
        'contact_name': 'Lavado de Alfombras Chile',
        'category': 'Limpieza',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Lavado de alfombras a domicilio en Maipú.',
        'description': 'Limpieza profesional de alfombras muro a muro y alfombras sueltas, con retiro y entrega. Atiende Maipú y Estación Central. Dato público encontrado para revisión y contacto.',
        'phone': '+56978757479',
        'whatsapp_number': '56978757479',
        'service_area': 'Maipú y Estación Central',
        'source_name': 'Lavado de Alfombras Chile',
        'source_url': 'https://www.lavadodealfombraschile.cl/maipu-estacion-central.php',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'El Jardinero',
        'contact_name': 'El Jardinero',
        'category': 'Jardinería',
        'commune': 'Maipú',
        'sector': 'Región Metropolitana',
        'short_description': 'Jardinería y mantención de áreas verdes.',
        'description': 'Servicio de jardinería, mantención de jardines, sistemas de riego, podas, fertilización, fumigación y cuidado de áreas verdes. Dato público encontrado para revisión y contacto.',
        'phone': '+56992518815',
        'whatsapp_number': '56992518815',
        'service_area': 'Región Metropolitana, validar cobertura exacta en Maipú',
        'source_name': 'El Jardinero',
        'source_url': 'https://eljardinero.cl/',
        'source_notes': 'Dato público encontrado en web. Contactar para confirmar cobertura en Maipú antes de activar.',
    },
    {
        'business_name': 'Jimmy Fernández Gasfitería y Destapes Maipú',
        'contact_name': 'Jimmy Fernández',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Gasfitería y destapes en Maipú.',
        'description': 'Servicio de destapes de alcantarillado, lavamanos, lavaplatos, piletas y otros trabajos de gasfitería. Dato público encontrado para revisión y contacto.',
        'phone': '+56967464520',
        'whatsapp_number': '56967464520',
        'service_area': 'Maipú y otras comunas de Santiago',
        'source_name': 'MaestroMaipu.cl',
        'source_url': 'https://maestromaipu.cl/servicios-de-gasfiteria/gasfiteria-y-destapes-maipu-3920/',
        'source_notes': 'Dato público encontrado en directorio. Contactar antes de activar.',
    },
    {
        'business_name': 'Edgardo Valdés Gasfiter Urgencias Maipú',
        'contact_name': 'Edgardo Valdés Cáceres',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Gasfiter urgencias y mantenciones generales en Maipú.',
        'description': 'Servicio de gasfitería de urgencia, instalación de sanitarios, calefont, tinas, cámaras de alcantarillado, red de agua potable, electricidad, estructuras metálicas y mantenciones generales. Dato público encontrado para revisión y contacto.',
        'phone': '+56975653590',
        'whatsapp_number': '56975653590',
        'service_area': 'Maipú y Región Metropolitana',
        'source_name': 'MaestroMaipu.cl',
        'source_url': 'https://maestromaipu.cl/servicios-de-gasfiteria/gasfiter-urgencias-maipu-3942/',
        'source_notes': 'Dato público encontrado en directorio. Contactar antes de activar.',
    },
    {
        'business_name': 'Climatización Rancagua - Atención Maipú',
        'contact_name': 'Climatización Rancagua',
        'category': 'Climatización',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Instalación, mantención y reparación de aire acondicionado en Maipú.',
        'description': 'Servicio de instalación, mantención, reparación y venta de aire acondicionado para hogares, comercio y oficinas en Maipú. Dato público encontrado para revisión y contacto.',
        'phone': '+56967345720',
        'whatsapp_number': '56967345720',
        'service_area': 'Maipú y comunas cercanas',
        'source_name': 'Climatización Rancagua',
        'source_url': 'https://www.climatizacionrancagua.cl/aire-acondicionado-en-maipu.php',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Cerrajero Amigo Maipú',
        'contact_name': 'Cerrajero Amigo',
        'category': 'Cerrajería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Cerrajero a domicilio 24 horas en Maipú.',
        'description': 'Servicio de cerrajería a domicilio para Maipú y Santiago. Dato público encontrado para revisión y contacto.',
        'phone': '+56962361491',
        'whatsapp_number': '56962361491',
        'service_area': 'Maipú y Santiago',
        'source_name': 'Cerrajero Amigo',
        'source_url': 'https://www.cerrajeroamigo.cl/maipu',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Cerrajería CIIF Maipú',
        'contact_name': 'Cerrajería CIIF',
        'category': 'Cerrajería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Cerrajero a domicilio en Maipú.',
        'description': 'Servicio de apertura de chapas, cambio de chapas y venta de cerraduras de seguridad. Dato público encontrado para revisión y contacto.',
        'phone': '+56961583641',
        'whatsapp_number': '56961583641',
        'service_area': 'Maipú',
        'source_name': 'Cerrajería CIIF',
        'source_url': 'https://cerrajeriaciif.cl/cerrajeros-en_maipu',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
]


class Command(BaseCommand):
    help = 'Sincroniza prestadores autorizados y nuevos prospectos publicos de Maipu.'

    def handle(self, *args, **options):
        errors = []
        authorized_updated = 0
        prospects_created = 0
        duplicates_skipped = 0

        commune = self._ensure_commune('Maipú')
        category_map = self._ensure_categories()

        for data in AUTHORIZED_PROVIDERS:
            try:
                self._upsert_provider(
                    data=data,
                    category_map=category_map,
                    commune=commune,
                    is_active=True,
                    is_verified=True,
                    is_featured=False,
                    data_status=Provider.AUTHORIZED,
                )
                authorized_updated += 1
            except Exception as exc:
                errors.append(f"{data.get('business_name', 'Sin nombre')}: {exc}")

        for data in NEW_PUBLIC_PROSPECTS:
            try:
                whatsapp_number = self._clean_phone(data['whatsapp_number'])
                exists = Provider.objects.filter(whatsapp_number=whatsapp_number).exists()
                provider, created = self._upsert_provider(
                    data=data,
                    category_map=category_map,
                    commune=commune,
                    is_active=False,
                    is_verified=False,
                    is_featured=False,
                    data_status=Provider.PUBLIC_PROSPECT,
                )
                if created:
                    prospects_created += 1
                elif exists:
                    duplicates_skipped += 1
                    self.stdout.write(self.style.WARNING(f"Duplicado actualizado/omitido como prospecto: {provider.business_name} ({whatsapp_number})"))
            except Exception as exc:
                errors.append(f"{data.get('business_name', 'Sin nombre')}: {exc}")

        self.stdout.write(self.style.SUCCESS(f'Autorizados actualizados: {authorized_updated}'))
        self.stdout.write(self.style.SUCCESS(f'Prospectos nuevos creados: {prospects_created}'))
        self.stdout.write(self.style.WARNING(f'Duplicados omitidos: {duplicates_skipped}'))
        self.stdout.write(self.style.ERROR(f'Errores: {len(errors)}'))
        for error in errors:
            self.stdout.write(self.style.ERROR(f'- {error}'))

    def _upsert_provider(self, data, category_map, commune, is_active, is_verified, is_featured, data_status):
        whatsapp_number = self._clean_phone(data['whatsapp_number'])
        provider, created = Provider.objects.update_or_create(
            whatsapp_number=whatsapp_number,
            defaults={
                'business_name': data['business_name'],
                'contact_name': data.get('contact_name') or data['business_name'],
                'category': category_map[data['category']],
                'commune': commune,
                'sector': data['sector'],
                'short_description': data['short_description'],
                'description': data['description'],
                'phone': data['phone'],
                'service_area': data['service_area'],
                'source_name': data['source_name'],
                'source_url': data['source_url'],
                'source_notes': data['source_notes'],
                'data_status': data_status,
                'is_active': is_active,
                'is_verified': is_verified,
                'is_featured': is_featured,
            },
        )
        return provider, created

    def _ensure_commune(self, name):
        commune, _ = Commune.objects.update_or_create(
            slug=slugify(name),
            defaults={'name': name, 'is_active': True},
        )
        return commune

    def _ensure_categories(self):
        categories = {
            'Cerrajería': ('Servicios de cerrajería, apertura y cambio de cerraduras.', 'CE'),
            'Gasfitería': ('Servicios de gasfitería, filtraciones, destapes y reparaciones.', 'GF'),
            'Electricidad': ('Servicios eléctricos domiciliarios y mantenciones.', 'EL'),
            'Climatización': ('Instalación y mantención de climatización.', 'CL'),
            'Construcción': ('Construcción, remodelaciones y trabajos generales.', 'CO'),
            'Limpieza': ('Limpieza domiciliaria, comercial y mantenciones.', 'LI'),
            'Jardinería': ('Jardinería, poda y mantención de áreas verdes.', 'JA'),
            'Carpintería': ('Muebles, puertas, ajustes y trabajos en madera.', 'CA'),
            'Pintura': ('Pintura interior, exterior y preparación de superficies.', 'PI'),
        }
        category_map = {}
        for index, (name, (description, icon)) in enumerate(categories.items(), start=1):
            category, _ = Category.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    'name': name,
                    'description': description,
                    'icon': icon,
                    'display_order': index,
                    'is_active': True,
                },
            )
            category_map[name] = category
        return category_map

    def _clean_phone(self, value):
        return ''.join(character for character in value if character.isdigit())
