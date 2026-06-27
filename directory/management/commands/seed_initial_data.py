from django.core.management.base import BaseCommand

from directory.models import Category, Commune, Provider


class Command(BaseCommand):
    help = 'Carga datos iniciales para SERVIPLACE Maipu.'

    def handle(self, *args, **options):
        maipu, _ = Commune.objects.update_or_create(
            slug='maipu',
            defaults={'name': 'Maipu', 'is_active': True},
        )

        categories = [
            ('Gasfiteria', 'gasfiteria', 'Reparaciones de agua, filtraciones y sanitarios.', 'GF'),
            ('Cerrajeria', 'cerrajeria', 'Apertura, cambio de chapas y urgencias.', 'CE'),
            ('Electricidad', 'electricidad', 'Instalaciones, tableros y reparaciones electricas.', 'EL'),
            ('Carpinteria', 'carpinteria', 'Muebles, puertas, ajustes y trabajos en madera.', 'CA'),
            ('Construccion', 'construccion', 'Obras menores, ampliaciones y terminaciones.', 'CO'),
            ('Limpieza', 'limpieza', 'Aseo profundo, mantencion y limpieza domiciliaria.', 'LI'),
            ('Jardineria', 'jardineria', 'Poda, riego, mantencion y recuperacion de jardines.', 'JA'),
            ('Climatizacion', 'climatizacion', 'Instalacion y mantencion de aire acondicionado.', 'CL'),
            ('Pintura', 'pintura', 'Pintura interior, exterior y reparacion de muros.', 'PI'),
        ]

        category_map = {}
        for order, (name, slug, description, icon) in enumerate(categories, start=1):
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': description,
                    'icon': icon,
                    'display_order': order,
                    'is_active': True,
                },
            )
            category_map[slug] = category

        providers = [
            {
                'business_name': 'Gasfiter Maipu Express',
                'contact_name': 'Carlos Munoz',
                'category': 'gasfiteria',
                'sector': 'Pajaritos',
                'short_description': 'Reparacion de filtraciones, WC, calefont y griferia.',
                'description': 'Atencion rapida para reparaciones domiciliarias de gasfiteria. Diagnostico claro, presupuesto antes de iniciar y trabajos en banos, cocinas y patios.',
                'phone': '+56 9 1111 0001',
                'whatsapp_number': '56911110001',
                'service_area': 'Maipu urbano y sectores cercanos',
                'is_verified': True,
                'is_featured': True,
            },
            {
                'business_name': 'Cerrajeria Los Heroes',
                'contact_name': 'Paula Rivas',
                'category': 'cerrajeria',
                'sector': 'Los Heroes',
                'short_description': 'Apertura de puertas, cambio de chapas y copias de llaves.',
                'description': 'Servicio de cerrajeria residencial y comercial para urgencias y mantenciones planificadas. Trabajo cuidadoso y orientado a seguridad.',
                'phone': '+56 9 1111 0002',
                'whatsapp_number': '56911110002',
                'service_area': 'Los Heroes, El Abrazo y Ciudad Satelite',
                'is_verified': True,
                'is_featured': True,
            },
            {
                'business_name': 'ElectroMaipu Servicios',
                'contact_name': 'Jorge Araya',
                'category': 'electricidad',
                'sector': 'Rinconada',
                'short_description': 'Instalaciones electricas, enchufes, luminarias y tablero.',
                'description': 'Electricista para hogares y locales pequenos. Revision de fallas, instalacion de luminarias, enchufes, automaticos y mejoras de seguridad.',
                'phone': '+56 9 1111 0003',
                'whatsapp_number': '56911110003',
                'service_area': 'Todo Maipu',
                'is_verified': True,
                'is_featured': False,
            },
            {
                'business_name': 'Carpinteria Don Raul',
                'contact_name': 'Raul Espinoza',
                'category': 'carpinteria',
                'sector': 'Ciudad Satelite',
                'short_description': 'Reparacion de muebles, puertas, closets y trabajos a medida.',
                'description': 'Carpinteria practica para mantenciones del hogar, ajustes de puertas, armado de muebles, repisas y soluciones a medida.',
                'phone': '+56 9 1111 0004',
                'whatsapp_number': '56911110004',
                'service_area': 'Ciudad Satelite y alrededores',
                'is_verified': False,
                'is_featured': False,
            },
            {
                'business_name': 'Maestros El Abrazo',
                'contact_name': 'Felipe Contreras',
                'category': 'construccion',
                'sector': 'El Abrazo',
                'short_description': 'Obras menores, tabiqueria, ceramica y terminaciones.',
                'description': 'Equipo para mejoras del hogar, reparaciones, ampliaciones pequenas, radieres, ceramica y terminaciones interiores.',
                'phone': '+56 9 1111 0005',
                'whatsapp_number': '56911110005',
                'service_area': 'El Abrazo, Los Bosquinos y Maipu poniente',
                'is_verified': True,
                'is_featured': True,
            },
            {
                'business_name': 'Limpieza Brillo Hogar',
                'contact_name': 'Andrea Soto',
                'category': 'limpieza',
                'sector': 'La Farfana',
                'short_description': 'Aseo profundo para casas, departamentos y oficinas pequenas.',
                'description': 'Limpieza por jornada, aseo post arriendo, limpieza de cocina, banos, vidrios y espacios comunes. Agenda flexible.',
                'phone': '+56 9 1111 0006',
                'whatsapp_number': '56911110006',
                'service_area': 'La Farfana, Rinconada y centro de Maipu',
                'is_verified': False,
                'is_featured': False,
            },
            {
                'business_name': 'Jardines Rinconada',
                'contact_name': 'Marcelo Fuentes',
                'category': 'jardineria',
                'sector': 'Rinconada',
                'short_description': 'Mantencion de jardines, poda, riego y retiro de ramas.',
                'description': 'Servicio de jardineria para casas y comunidades pequenas. Mantencion mensual, recuperacion de jardines y poda responsable.',
                'phone': '+56 9 1111 0007',
                'whatsapp_number': '56911110007',
                'service_area': 'Rinconada, Pajaritos y Maipu centro',
                'is_verified': True,
                'is_featured': False,
            },
            {
                'business_name': 'ClimaSur Maipu',
                'contact_name': 'Nicolas Vera',
                'category': 'climatizacion',
                'sector': 'Las Naciones',
                'short_description': 'Instalacion, mantencion y limpieza de aire acondicionado.',
                'description': 'Tecnico en climatizacion para equipos split, mantencion preventiva, limpieza y diagnostico de fallas.',
                'phone': '+56 9 1111 0008',
                'whatsapp_number': '56911110008',
                'service_area': 'Maipu y Cerrillos previa coordinacion',
                'is_verified': True,
                'is_featured': True,
            },
            {
                'business_name': 'Pinturas Nueva San Martin',
                'contact_name': 'Sergio Molina',
                'category': 'pintura',
                'sector': 'Nueva San Martin',
                'short_description': 'Pintura interior y exterior con preparacion de superficies.',
                'description': 'Trabajos de pintura para casas, departamentos y locales. Reparacion menor de muros, lijado, sellado y terminaciones limpias.',
                'phone': '+56 9 1111 0009',
                'whatsapp_number': '56911110009',
                'service_area': 'Todo Maipu',
                'is_verified': False,
                'is_featured': False,
            },
            {
                'business_name': 'Electricidad Segura Maipu',
                'contact_name': 'Camila Paredes',
                'category': 'electricidad',
                'sector': 'Maipu Centro',
                'short_description': 'Revision de instalaciones, enchufes, luminarias y protecciones.',
                'description': 'Atencion para hogares que necesitan mejorar seguridad electrica, instalar puntos nuevos o resolver cortes y fallas intermitentes.',
                'phone': '+56 9 1111 0010',
                'whatsapp_number': '56911110010',
                'service_area': 'Maipu centro, Pajaritos y Las Parcelas',
                'is_verified': True,
                'is_featured': False,
            },
        ]

        created_or_updated = 0
        for data in providers:
            category_slug = data.pop('category')
            Provider.objects.update_or_create(
                business_name=data['business_name'],
                defaults={
                    **data,
                    'category': category_map[category_slug],
                    'commune': maipu,
                    'is_active': True,
                },
            )
            created_or_updated += 1

        self.stdout.write(self.style.SUCCESS(f'Datos iniciales cargados: 1 comuna, {len(categories)} categorias, {created_or_updated} prestadores.'))
