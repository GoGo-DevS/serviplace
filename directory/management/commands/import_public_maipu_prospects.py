from django.core.management.base import BaseCommand
from django.utils.text import slugify

from directory.models import Category, Commune, Provider


PROSPECTS = [
    {
        'business_name': 'Cerrajero Vega Maipú',
        'contact_name': 'Cerrajero Vega',
        'category': 'Cerrajería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Servicio de cerrajería a domicilio en Maipú.',
        'description': 'Apertura de puertas, autos, cambio de cerraduras y atención de urgencias en Maipú. Dato público encontrado para revisión y contacto.',
        'phone': '+56992391520',
        'whatsapp_number': '56992391520',
        'service_area': 'Maipú y sectores cercanos',
        'source_name': 'Cerrajero Vega',
        'source_url': 'https://cerrajerovega.cl/cerrajero-en-maipu',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Alo Cerrajero Maipú',
        'contact_name': 'Alo Cerrajero',
        'category': 'Cerrajería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Cerrajero a domicilio en Maipú.',
        'description': 'Servicio de cerrajería a domicilio, apertura y cambio de chapas. Dato público encontrado para revisión y contacto.',
        'phone': '+56950195849',
        'whatsapp_number': '56950195849',
        'service_area': 'Maipú',
        'source_name': 'Alo Cerrajero',
        'source_url': 'https://www.alocerrajero.cl/maipu.html',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Cerrajería Ibáñez Maipú',
        'contact_name': 'Cerrajería Ibáñez',
        'category': 'Cerrajería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Cerrajería 24/7 con cobertura en Maipú.',
        'description': 'Apertura de puertas, cambio de cerraduras, cerrajería automotriz, cajas fuertes y servicios de seguridad. Dato público encontrado para revisión y contacto.',
        'phone': '+56989758412',
        'whatsapp_number': '56989758412',
        'service_area': 'Maipú y Región Metropolitana',
        'source_name': 'Cerrajería Ibáñez',
        'source_url': 'https://cerrajeroibanez.cl/cerrajero-en-maipu/',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Grifería Carola',
        'contact_name': 'Grifería Carola',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Gasfitería y grifería local en Maipú.',
        'description': 'Local de gasfitería y grifería en Maipú. Dato público encontrado para revisión y contacto.',
        'phone': '+56989920770',
        'whatsapp_number': '56989920770',
        'service_area': 'Maipú',
        'source_name': 'Grifería Carola',
        'source_url': 'https://griferiacarola.cl/',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Cumbre Partner Gasfiter Maipú',
        'contact_name': 'Cumbre Partner',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Gasfiter a domicilio en Maipú.',
        'description': 'Reparaciones, destapes, filtraciones, calefont, cañerías e instalaciones. Dato público encontrado para revisión y contacto.',
        'phone': '+56962234483',
        'whatsapp_number': '56962234483',
        'service_area': 'Maipú',
        'source_name': 'Cumbre Partner',
        'source_url': 'https://www.cumbrepartner.com/gasfiter-maipu/',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Plomero.cl Maipú',
        'contact_name': 'Plomero.cl',
        'category': 'Gasfitería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Gasfitería profesional a domicilio en Maipú.',
        'description': 'Servicio de gasfitería para urgencias, fugas, rebalses, filtraciones y mantenciones. Dato público encontrado para revisión y contacto.',
        'phone': '+56961913434',
        'whatsapp_number': '56961913434',
        'service_area': 'Maipú y Gran Santiago',
        'source_name': 'Plomero.cl',
        'source_url': 'https://plomero.cl/comunas/gasfiter-en-maipu/',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'Soluciones Eléctricas CL Maipú',
        'contact_name': 'Soluciones Eléctricas CL',
        'category': 'Electricidad',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Electricista a domicilio en Maipú.',
        'description': 'Emergencias eléctricas, revisiones, mantenciones, tableros, enchufes, iluminación y trabajos certificados. Dato público encontrado para revisión y contacto.',
        'phone': '+56972361592',
        'whatsapp_number': '56972361592',
        'service_area': 'Maipú y Región Metropolitana',
        'source_name': 'Soluciones Eléctricas CL',
        'source_url': 'https://solucionelectricas.cl/electricista-en-maipu/',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'MegaClima Maipú',
        'contact_name': 'MegaClima',
        'category': 'Climatización',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Mantención de aire acondicionado en Maipú.',
        'description': 'Mantención preventiva de aire acondicionado split, multisplit e inverter. Dato público encontrado para revisión y contacto.',
        'phone': '+56923977662',
        'whatsapp_number': '56923977662',
        'service_area': 'Maipú',
        'source_name': 'MegaClima',
        'source_url': 'https://www.megaclima.cl/mantencion-de-aire-acondicionado-en-maipu',
        'source_notes': 'Dato público encontrado en web. Contactar antes de activar.',
    },
    {
        'business_name': 'José Maestro Sureño',
        'contact_name': 'José Maestro Sureño',
        'category': 'Construcción',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Maestro constructor en Maipú.',
        'description': 'Construcción, remodelación, ampliaciones, cerámicas, electricidad, gasfitería, cobertizos, estructuras metálicas y pintura. Dato público encontrado para revisión y contacto.',
        'phone': '+56998601170',
        'whatsapp_number': '56998601170',
        'service_area': 'Maipú y Santiago',
        'source_name': 'Perfil Comercial',
        'source_url': 'https://perfilcomercial.cl/listing/electrico-ampliaciones-gasfiter-maipu/',
        'source_notes': 'Dato público encontrado en directorio. Contactar antes de activar.',
    },
    {
        'business_name': 'Construcciones y Remodelaciones',
        'contact_name': 'Construcciones y Remodelaciones',
        'category': 'Construcción',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Construcciones y remodelaciones en Maipú.',
        'description': 'Construcciones, remodelaciones, ampliaciones y trabajos generales. Dato público encontrado para revisión y contacto.',
        'phone': '+56968453133',
        'whatsapp_number': '56968453133',
        'service_area': 'Maipú',
        'source_name': 'Maipú a su Servicio',
        'source_url': 'https://maipuasuservicio.cl/construcciones-y-remodelaciones/',
        'source_notes': 'Dato público encontrado en directorio local. Contactar antes de activar.',
    },
    {
        'business_name': 'Renovación de Propiedades',
        'contact_name': 'Renovación de Propiedades',
        'category': 'Limpieza',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Renovación, pintura y limpieza de alfombras.',
        'description': 'Servicios de papel mural, pisos, pintura y limpieza de alfombras. Dato público encontrado para revisión y contacto.',
        'phone': '+56936585846',
        'whatsapp_number': '56936585846',
        'service_area': 'Maipú',
        'source_name': 'Maipú a su Servicio',
        'source_url': 'https://maipuasuservicio.cl/renovacion-de-propiedades/',
        'source_notes': 'Dato público encontrado en directorio local. Contactar antes de activar.',
    },
    {
        'business_name': 'Jardinería Maipú',
        'contact_name': 'Jardinería Maipú',
        'category': 'Jardinería',
        'commune': 'Maipú',
        'sector': 'Maipú',
        'short_description': 'Mantención de jardines y áreas verdes.',
        'description': 'Servicio de jardinería, mantención de áreas verdes y fumigación. Dato público encontrado para revisión y contacto.',
        'phone': '+56951597516',
        'whatsapp_number': '56951597516',
        'service_area': 'Maipú',
        'source_name': 'Jardinería Maipú',
        'source_url': 'https://www.instagram.com/jardineriamaipu/',
        'source_notes': 'Dato público encontrado en perfil/red social pública. Contactar antes de activar.',
    },
]


class Command(BaseCommand):
    help = 'Importa prospectos publicos de prestadores de Maipu para revision manual.'

    def handle(self, *args, **options):
        commune = self._ensure_commune('Maipú')
        category_map = self._ensure_categories()
        created = 0
        skipped = 0

        for prospect in PROSPECTS:
            whatsapp_number = self._clean_phone(prospect['whatsapp_number'])
            if Provider.objects.filter(whatsapp_number=whatsapp_number).exists():
                skipped += 1
                continue

            Provider.objects.create(
                business_name=prospect['business_name'],
                contact_name=prospect['contact_name'],
                category=category_map[prospect['category']],
                commune=commune,
                sector=prospect['sector'],
                short_description=prospect['short_description'],
                description=prospect['description'],
                phone=prospect['phone'],
                whatsapp_number=whatsapp_number,
                service_area=prospect['service_area'],
                source_name=prospect['source_name'],
                source_url=prospect['source_url'],
                source_notes=prospect['source_notes'],
                data_status=Provider.PUBLIC_PROSPECT,
                is_verified=False,
                is_featured=False,
                is_active=False,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Prospectos creados: {created}'))
        self.stdout.write(self.style.WARNING(f'Prospectos omitidos por duplicado: {skipped}'))

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
