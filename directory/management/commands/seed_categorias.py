"""
Crea las categorías base si no existen. Idempotente y NO pisa: si la categoría
ya existe no le cambia nombre, descripción, icono ni grupo (eso se edita en el
admin). Corre en cada build: una base nueva arranca sin las categorías que no
vienen en el fixture inicial, y sin ellas no se puede publicar en ese rubro.

17-10-2026 — Se suman los profesionales independientes (salud, clases,
belleza, servicios profesionales). Las 9 de oficios del hogar quedan en el
grupo "hogar", que es el valor por defecto de la columna.
"""
from django.core.management.base import BaseCommand

from directory.models import Category

# Nombre de búsqueda (SEO): lo que la gente escribe en Google.
SEO_NOMBRES = {
    'gasfiteria': 'Gásfiter',
    'electricidad': 'Electricista',
    'cerrajeria': 'Cerrajero',
    'climatizacion': 'Técnico en climatización',
    'construccion': 'Maestro constructor',
    'soldadura': 'Soldador',
    'limpieza': 'Servicio de aseo',
    'jardineria': 'Jardinero',
    'carpinteria': 'Carpintero',
    'pintura': 'Pintor',
    'kinesiologia': 'Kinesiólogo',
    'psicologia': 'Psicólogo',
    'nutricion': 'Nutricionista',
    'fonoaudiologia': 'Fonoaudiólogo',
    'terapia-ocupacional': 'Terapeuta ocupacional',
    'enfermeria': 'Enfermería a domicilio',
    'podologia': 'Podólogo',
    'cuidado-de-personas': 'Cuidadora de adulto mayor',
    'clases-particulares': 'Profesor particular',
    'idiomas': 'Clases de inglés e idiomas',
    'clases-de-musica': 'Profesor de música',
    'psicopedagogia': 'Psicopedagogo',
    'peluqueria': 'Peluquería a domicilio',
    'manicure-y-estetica': 'Manicurista',
    'contabilidad': 'Contador',
    'diseno-grafico': 'Diseñador gráfico',
    'fotografia-y-video': 'Fotógrafo',
    'soporte-computacional': 'Técnico en computación',
    'desarrollo-web': 'Desarrollador web',
    'tatuajes': 'Tatuador',
    'seguridad-hogar': 'Instalador de seguridad',
    'repuestos-automotrices': 'Repuestos automotrices',
    'automotoras': 'Automotora',
    'uniformes-y-ropa-de-trabajo': 'Tienda de uniformes',
    'reposteria-y-dulces': 'Repostería',
    'fletes-y-logistica': 'Fletes',
    'traslados-y-turismo': 'Transporte de pasajeros',
}

H, S, E, B, P, T = (Category.HOGAR, Category.SALUD, Category.EDUCACION,
                    Category.BELLEZA, Category.PROFESIONAL, Category.TIENDAS)
TR = Category.TRANSPORTE

# (slug, nombre, descripción, icono, grupo, pide_registro_salud)
CATEGORIAS = [
    ('gasfiteria', 'Gasfitería', 'Filtraciones, calefont, WC, grifería y destapes.', '🔧', H, False),
    ('electricidad', 'Electricidad', 'Instalaciones, tableros, enchufes y reparaciones eléctricas.', '⚡', H, False),
    ('cerrajeria', 'Cerrajería', 'Apertura de puertas, cambio de chapas y copias de llaves.', '🔐', H, False),
    ('climatizacion', 'Climatización', 'Instalación y mantención de aire acondicionado y calefacción.', '❄️', H, False),
    ('construccion', 'Construcción', 'Obras menores, ampliaciones, remodelaciones y terminaciones.', '🏗️', H, False),
    ('soldadura', 'Soldadura', 'Rejas, portones, estructuras metálicas y reparaciones en fierro.', '🔩', H, False),
    ('limpieza', 'Limpieza', 'Aseo domiciliario, de oficinas y post obra.', '🧹', H, False),
    ('jardineria', 'Jardinería', 'Poda, riego, pasto y mantención de jardines.', '🌿', H, False),
    ('carpinteria', 'Carpintería', 'Muebles, puertas, closets y trabajos en madera.', '🪚', H, False),
    ('pintura', 'Pintura', 'Pintura interior, exterior y reparación de muros.', '🎨', H, False),
    ('seguridad-hogar', 'Seguridad para el hogar', 'Alarmas, cámaras, cercos y salas de resguardo para tu casa.', '🛡️', H, False),

    ('kinesiologia', 'Kinesiología', 'Rehabilitación, lesiones deportivas, kinesiología respiratoria y a domicilio.', '💪', S, True),
    ('psicologia', 'Psicología', 'Terapia individual, de pareja e infanto-juvenil, presencial u online.', '🧠', S, True),
    ('nutricion', 'Nutrición', 'Planes de alimentación, control de peso y nutrición deportiva.', '🥗', S, True),
    ('fonoaudiologia', 'Fonoaudiología', 'Lenguaje, habla, voz, deglución y audición.', '🗣️', S, True),
    ('terapia-ocupacional', 'Terapia ocupacional', 'Autonomía, integración sensorial y rehabilitación funcional.', '🧩', S, True),
    ('enfermeria', 'Enfermería a domicilio', 'Curaciones, inyecciones, control de signos y cuidados post operatorios.', '💉', S, True),
    ('podologia', 'Podología', 'Cuidado de pies, uñas encarnadas y pie diabético.', '🦶', S, True),
    ('cuidado-de-personas', 'Cuidado de personas', 'Cuidado de adultos mayores, acompañamiento y apoyo en el hogar.', '🤝', S, False),

    ('clases-particulares', 'Clases particulares', 'Matemática, lenguaje, ciencias, reforzamiento y preparación PAES.', '📚', E, False),
    ('idiomas', 'Idiomas', 'Inglés y otros idiomas para niños, adultos y empresas.', '🌎', E, False),
    ('clases-de-musica', 'Clases de música', 'Guitarra, piano, canto y otros instrumentos.', '🎸', E, False),
    ('psicopedagogia', 'Psicopedagogía', 'Apoyo en dificultades de aprendizaje y técnicas de estudio.', '✏️', E, False),

    ('peluqueria', 'Peluquería y barbería', 'Cortes, color y peinados, en local o a domicilio.', '💇', B, False),
    ('manicure-y-estetica', 'Manicure y estética', 'Manicure, pedicure, pestañas, cejas y tratamientos faciales.', '💅', B, False),
    # 18-10-2026: para los clientes de GoGoDevS que no calzaban en ninguna.
    ('tatuajes', 'Tatuajes y piercing', 'Tatuajes con diseño propio, cover, retoques y piercing.', '🖋️', B, False),

    ('contabilidad', 'Contabilidad y trámites', 'Inicio de actividades, contabilidad para pymes, declaraciones y trámites.', '📊', P, False),
    ('diseno-grafico', 'Diseño gráfico', 'Logos, redes sociales, material impreso e identidad de marca.', '🖌️', P, False),
    ('fotografia-y-video', 'Fotografía y video', 'Eventos, productos, retratos y contenido para redes.', '📷', P, False),
    ('soporte-computacional', 'Soporte computacional', 'Reparación de computadores, redes, respaldos y formateo.', '💻', P, False),
    ('desarrollo-web', 'Desarrollo web y apps', 'Sitios web, tiendas online, apps y sistemas a medida para negocios.', '🌐', P, False),

    ('fletes-y-logistica', 'Fletes y logística', 'Fletes, mudanzas, transporte de carga y logística para empresas.', '🚚', TR, False),
    ('traslados-y-turismo', 'Traslados y turismo', 'Traslados al aeropuerto, tours y transporte de pasajeros para eventos y empresas.', '🚐', TR, False),

    ('repuestos-automotrices', 'Repuestos automotrices', 'Repuestos y accesorios para autos, camionetas y 4x4, con local o despacho.', '🔩', T, False),
    ('automotoras', 'Automotoras', 'Venta de vehículos, con financiamiento y recepción en parte de pago.', '🚙', T, False),
    ('uniformes-y-ropa-de-trabajo', 'Uniformes y ropa de trabajo', 'Uniformes clínicos y ropa de trabajo, en tienda o con despacho.', '🥼', T, False),
    ('reposteria-y-dulces', 'Repostería y dulces', 'Tortas, alfajores y dulces por encargo, con retiro o despacho.', '🧁', T, False),
]


class Command(BaseCommand):
    help = 'Crea las categorías base si faltan (idempotente, no sobreescribe).'

    def handle(self, *args, **options):
        creadas = 0
        for orden, (slug, nombre, desc, icono, grupo, salud) in enumerate(CATEGORIAS, start=1):
            _, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': nombre, 'description': desc, 'icon': icono, 'group': grupo,
                    'pide_registro_salud': salud, 'display_order': orden, 'is_active': True,
                    'seo_nombre': SEO_NOMBRES.get(slug, ''),
                },
            )
            creadas += int(created)
        self.stdout.write(f'Categorías: {creadas} creadas, {Category.objects.count()} en total.')
