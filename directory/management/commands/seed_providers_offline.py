"""
SOLO DESARROLLO — NUNCA EN UN BUILD NI EN PRODUCCIÓN.
Seed offline: genera providers FICTICIOS para 10 comunas grandes de Chile.
No requiere Google Maps API — usa datos ficticios pero plausibles.
Uso: python manage.py seed_providers_offline [--clear]
"""
import random

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from directory.models import Category, Commune, Provider

NOMBRES_EMPRESAS = {
    'Gasfitería': [
        'Soluciones Sanitarias', 'GasFit Express', 'Plomería Total',
        'Reparaciones Rápidas', 'Cañerías Pro', 'Instalaciones Modernas',
        'Gasfiter 24/7', 'Arreglos al Día', 'Fontanería Confiable', 'AguaTec',
        'HidroFix', 'Servicios Sanitarios Sur', 'Plomería Familiar', 'FlujoLibre',
    ],
    'Electricidad': [
        'Instalaciones Eléctricas', 'Luz y Corriente', 'ElectroFix',
        'Circuito Seguro', 'Watts Pro', 'Electricidad Confiable',
        'Ampere Servicios', 'Redes Eléctricas', 'VoltTec', 'PowerFix Chile',
        'Instalaciones Hogareñas', 'Electricista Express', 'Corriente Directa', 'BrioCorriente',
    ],
    'Cerrajería': [
        'Cerrajería 24H', 'Llaves y Cerraduras', 'AbrePuertas',
        'Seguridad Total', 'CerraTec', 'Llaves Maestras',
        'Apertura Rápida', 'Cerrajero Confiable', 'LlaveMaestra', 'Cerraduras Pro',
        'AccesoSeguro', 'Cerrajería Familiar', 'KeyFix', 'MásterKey',
    ],
    'Limpieza': [
        'Limpieza Profunda', 'SpotlessHome', 'CleanPro',
        'Aseo Express', 'LimpiaTodo', 'BrilloTotal',
        'Servicio de Aseo', 'CleanHouse', 'EcoLimpieza', 'Limpieza Garantizada',
        'Brillo Hogar', 'Pulcritud Servicios', 'LimpioYa', 'FamilyClean',
    ],
    'Climatización': [
        'Clima Confort', 'AireFresc', 'TermoTec',
        'Instalación de Aires', 'FríoCalor Pro', 'ClimaTech',
        'Refrigeración Total', 'AireAcondicionado24', 'TempFix', 'ClimaExpress',
        'AirMaster', 'TermoConfort', 'FrescoHogar', 'AireSeguro',
    ],
    'Construcción': [
        'Obras y Remodelaciones', 'ConstruFácil', 'Maestro Constructor',
        'Remodelaciones Express', 'ObrasPlus', 'Remodelaciones y Más',
        'Construcciones Familiares', 'ArquiTec', 'HogarNuevo', 'ReformasPro',
        'ConstruCasa', 'Obra Maestra', 'Remodelar Fácil', 'CasaNueva',
    ],
    'Jardinería': [
        'Verde y Lindo', 'JardinPro', 'Poda y Jardín',
        'EcoJardín', 'GreenCare', 'Plantas y Podas',
        'JardinExpress', 'Naturaleza Viva', 'GardenFix', 'Paisajismo Simple',
        'Jardín Perfecto', 'CésedPro', 'VerdeHogar', 'PlantasYa',
    ],
    'Carpintería': [
        'Muebles y Maderas', 'CarpinTec', 'Arte en Madera',
        'Terminaciones Finas', 'Muebles Express', 'Madera Viva',
        'El Carpintero', 'DiseñoEnMadera', 'TablaPlus', 'MaderaPro',
        'CasaMuebles', 'ArtesanoMadera', 'CarpinFácil', 'MaderaYa',
    ],
    'Pintura': [
        'Pinturas Express', 'ColorHogar', 'PinturaFina',
        'El Pintor', 'Brocha Maestro', 'Pintamos Todo',
        'PintoPro', 'PintadoYa', 'PinturaConfiable', 'ColorTotal',
        'BrochaZo', 'PinturaRápida', 'CasaColorida', 'PinturaHogar',
    ],
}

COMUNAS_OBJETIVO = [
    'Santiago', 'Maipú', 'Puente Alto', 'La Florida', 'Las Condes',
    'Ñuñoa', 'Providencia', 'Viña del Mar', 'Valparaíso', 'Concepción',
]

SECTORES_POR_COMUNA = {
    'Santiago': ['Centro', 'Barrio Lastarria', 'Yungay', 'Brasil', 'Concha y Toro', 'San Borja'],
    'Maipú': ['Ciudad de los Valles', 'Pajaritos', 'Las Viñitas', 'Rinconada', 'Tres Poniente', 'Villa Francia'],
    'Puente Alto': ['Valle Grande', 'El Llano', 'Condominio Santa Elena', 'Cabildo', 'Bajos de Mena'],
    'La Florida': ['Rojas Magallanes', 'El Bosque', 'Las Américas', 'Larrañaga', 'Vicuña Mackenna'],
    'Las Condes': ['El Golf', 'Vitacura', 'Lo Barnechea', 'Chicureo', 'Las Tranqueras'],
    'Ñuñoa': ['Irarrázaval', 'Plaza Ñuñoa', 'Macul', 'Franklin', 'Grecia'],
    'Providencia': ['Barrio Italia', 'Manuel Montt', 'Pedro de Valdivia', 'Los Leones'],
    'Viña del Mar': ['Recreo', 'Achupallas', 'Reñaca', 'Villa Dulce', 'Forestal'],
    'Valparaíso': ['Cerro Alegre', 'Cerro Concepción', 'El Almendral', 'Barón', 'Playa Ancha'],
    'Concepción': ['Barrio Universitario', 'Hualpén', 'Chiguayante', 'San Pedro', 'Lorenzo Arenas'],
}

CONTACTOS = [
    'Roberto Sánchez', 'María González', 'Juan Pérez', 'Claudia Torres',
    'Felipe Muñoz', 'Patricia Lagos', 'Andrés Rodríguez', 'Verónica Fuentes',
    'Pablo Morales', 'Ana Vargas', 'Carlos Díaz', 'Lorena Martínez',
    'Diego Castro', 'Marcela Jiménez', 'Héctor Navarro', 'Sandra Reyes',
    'Fernando Álvarez', 'Carla Herrera', 'Rodrigo Ramos', 'Pilar Medina',
]

DESCRIPCIONES_CORTAS = {
    'Gasfitería': [
        'Gasfiter profesional con más de 10 años de experiencia en instalaciones y reparaciones.',
        'Reparación de cañerías, filtraciones y todo tipo de problemas sanitarios.',
        'Instalación de calefont, termos y griferías. Atención rápida y garantizada.',
        'Gasfitería general y de emergencia. Trabajo garantizado y materiales incluidos.',
    ],
    'Electricidad': [
        'Electricista certificado. Instalaciones residenciales y comerciales con garantía.',
        'Reparación de cortocircuitos, instalación de enchufes y tableros eléctricos.',
        'Electricidad general. Certificación SEC disponible. Trabajo limpio y seguro.',
        'Instalaciones y reparaciones eléctricas. Presupuesto sin costo.',
    ],
    'Cerrajería': [
        'Apertura de puertas 24/7. Cambio de chapa y duplicado de llaves.',
        'Cerrajero urgente. Apertura sin daños, cambio de cilindros y chapas.',
        'Servicio de cerrajería rápido. Abrimos cualquier tipo de puerta.',
        'Instalación y reparación de cerraduras de seguridad. Atención inmediata.',
    ],
    'Limpieza': [
        'Limpieza de hogares, oficinas y post-construcción. Personal de confianza.',
        'Aseo profundo residencial y comercial. Equipos profesionales.',
        'Servicio de limpieza doméstica. Flexibilidad de horarios.',
        'Limpieza de fin de obra y mudanza. Resultado garantizado.',
    ],
    'Climatización': [
        'Instalación y mantención de aires acondicionados. Todas las marcas.',
        'Servicio técnico en climatización. Carga de gas y limpieza de filtros.',
        'Instalación de minisplit y aires de ventana. Trabajo garantizado.',
        'Mantención preventiva y correctiva de sistemas de climatización.',
    ],
    'Construcción': [
        'Remodelaciones de cocinas, baños y pisos. Presupuesto sin costo.',
        'Obras menores y remodelaciones. Maestro con amplia experiencia.',
        'Instalación de pisos flotantes, cerámica y porcelana.',
        'Remodelaciones integrales. Coordinación y trabajo de calidad.',
    ],
    'Jardinería': [
        'Poda de árboles, mantención de jardines y retiro de escombros verdes.',
        'Diseño y mantención de jardines residenciales. Trabajo de calidad.',
        'Cortadora de pasto, poda y limpieza general del jardín.',
        'Servicio de jardinería periódico. Plantas sanas y jardín impecable.',
    ],
    'Carpintería': [
        'Fabricación de muebles a medida y reparaciones de madera.',
        'Instalación de puertas, ventanas y muebles empotrados.',
        'Carpintería fina. Diseño personalizado con presupuesto sin costo.',
        'Reparación de muebles y puertas. Trabajo prolijo y rápido.',
    ],
    'Pintura': [
        'Pintura de casas, departamentos y oficinas. Materiales incluidos.',
        'Pintor profesional. Terminación impecable y limpieza post-trabajo.',
        'Pintura interior y exterior. Presupuesto gratuito sin compromiso.',
        'Pintura al agua y esmalte. Trabajo garantizado.',
    ],
}

DESCRIPCIONES_LARGAS = {
    'Gasfitería': 'Ofrezco servicio de gasfitería profesional en tu comuna. Instalación y reparación de cañerías, filtraciones, calefont, termos y griferías. Trabajo rápido, limpio y garantizado. Materiales incluidos en la mayoría de los trabajos. Emito boleta.',
    'Electricidad': 'Electricista certificado con experiencia en instalaciones residenciales y comerciales. Realizo instalación de enchufes, interruptores, tableros eléctricos, luminarias y mucho más. Trabajo seguro y ordenado. Certificación SEC disponible para ampliaciones.',
    'Cerrajería': 'Servicio de cerrajería disponible cuando lo necesites. Apertura de puertas sin daños, cambio de cilindros, instalación de chapas de seguridad y duplicado de llaves. Rápido, discreto y confiable.',
    'Limpieza': 'Servicio de limpieza profesional para tu hogar u oficina. Personal con experiencia y referencias verificables. Traigo todos los implementos necesarios. Disponibilidad de lunes a sábado. Presupuesto según metros cuadrados.',
    'Climatización': 'Instalación, mantención y reparación de sistemas de climatización. Trabajo con todas las marcas: Samsung, LG, Midea, Carrier, Daikin y más. Carga de gas refrigerante y limpieza profunda de filtros incluida en la mantención.',
    'Construcción': 'Maestro constructor con más de 15 años de experiencia. Remodelaciones de cocinas, baños, living y dormitorios. Instalación de revestimientos, cielos falsos, tabiques y mucho más. Entrego presupuesto detallado sin costo.',
    'Jardinería': 'Servicio de mantención de jardines y áreas verdes. Corte de césped, poda de árboles y arbustos, abono, riego y retiro de residuos vegetales. Equipos propios. Disponible para trabajos únicos o contratos mensuales.',
    'Carpintería': 'Carpintero con taller propio. Fabricación de muebles a medida, clósets, cocinas, escaleras y todo tipo de estructuras de madera. Instalación de pisos de madera y puertas. Diseños personalizados con presupuesto sin costo.',
    'Pintura': 'Pintor profesional con más de 12 años de experiencia. Pintura de interiores y exteriores con materiales de primera calidad. Incluye preparación de superficies, sellado y terminación impecable. Emito boleta y entrego garantía por escrito.',
}


def telefono_falso():
    prefijos = ['2', '9']
    if random.choice(prefijos) == '9':
        return f'+569{random.randint(10000000, 99999999)}'
    return f'+562{random.randint(1000000, 9999999)}'

def _solo_desarrollo(command, options):
    """Este seed inventa prestadores. JAMÁS en un build ni en producción."""
    from django.conf import settings
    import os
    if os.environ.get('RENDER') or not settings.DEBUG or not options.get('solo_desarrollo'):
        command.stderr.write(command.style.ERROR(
            'Este comando crea datos FALSOS. Solo corre en desarrollo (DEBUG=True, sin RENDER) '
            'y con --solo-desarrollo explícito. No va en build.sh.'
        ))
        return False
    return True


class Command(BaseCommand):
    help = 'Seed offline: genera providers realistas sin Google Maps API'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Eliminar providers scrapeados antes de insertar')
        parser.add_argument('--por-comuna', type=int, default=20, help='Providers por comuna (default: 20)')
        parser.add_argument('--solo-desarrollo', action='store_true', help='Obligatorio: confirma que es una base de desarrollo.')

    def handle(self, *args, **options):
        if not _solo_desarrollo(self, options):
            return
        if options['clear']:
            deleted, _ = Provider.objects.filter(data_status=Provider.PUBLIC_PROSPECT, owner__isnull=True).exclude(
                commune__name='Maipú'
            ).delete()
            self.stdout.write(self.style.WARNING(f'Eliminados {deleted} providers previos.'))

        categories = {c.name: c for c in Category.objects.filter(is_active=True)}
        communes = {c.name: c for c in Commune.objects.filter(is_active=True)}

        missing_comunas = [c for c in COMUNAS_OBJETIVO if c not in communes]
        if missing_comunas:
            self.stdout.write(self.style.WARNING(f'Comunas no encontradas en BD: {missing_comunas}'))

        total_created = 0
        por_comuna = options['por_comuna']
        cat_names = list(NOMBRES_EMPRESAS.keys())

        for comuna_name in COMUNAS_OBJETIVO:
            commune = communes.get(comuna_name)
            if not commune:
                continue

            sectores = SECTORES_POR_COMUNA.get(comuna_name, ['Centro', 'Sur', 'Norte'])
            created_in_commune = 0

            for cat_name in cat_names:
                category = categories.get(cat_name)
                if not category:
                    continue

                nombres = NOMBRES_EMPRESAS[cat_name]
                desc_cortas = DESCRIPCIONES_CORTAS[cat_name]
                desc_larga = DESCRIPCIONES_LARGAS[cat_name]
                per_category = max(1, por_comuna // len(cat_names))

                for _ in range(per_category):
                    nombre = random.choice(nombres)
                    sufijo = random.choice(['', ' SpA', ' Ltda', ' Chile', ' & Cia', ''])
                    business_name = f'{nombre}{sufijo} {comuna_name}'[:140]
                    contacto = random.choice(CONTACTOS)
                    sector = random.choice(sectores)
                    tel = telefono_falso()
                    desc_corta = random.choice(desc_cortas)

                    existe = Provider.objects.filter(
                        business_name=business_name,
                        commune=commune,
                    ).exists()
                    if existe:
                        continue

                    Provider.objects.create(
                        business_name=business_name,
                        contact_name=contacto,
                        category=category,
                        commune=commune,
                        sector=sector,
                        short_description=desc_corta,
                        description=desc_larga,
                        phone=tel,
                        whatsapp_number=tel.replace('+56', '56').replace('+', ''),
                        service_area=f'{comuna_name} y comunas cercanas',
                        data_status=Provider.PUBLIC_PROSPECT,
                        is_active=True,
                        source_name='seed_offline',
                        source_notes='Dato sintético — reemplazar con datos reales al reclamar.',
                    )
                    created_in_commune += 1
                    total_created += 1

            self.stdout.write(f'  {comuna_name}: {created_in_commune} providers')

        self.stdout.write(self.style.SUCCESS(f'\nTotal creados: {total_created} providers'))
        self.stdout.write('Recuerda: estos son datos sintéticos para demostración.')
        self.stdout.write('Reemplazar con datos reales de Google Maps cuando tengas GOOGLE_MAPS_API_KEY.')
