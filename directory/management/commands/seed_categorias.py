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

H, S, E, B, P = (Category.HOGAR, Category.SALUD, Category.EDUCACION,
                 Category.BELLEZA, Category.PROFESIONAL)

# (slug, nombre, descripción, icono, grupo, pide_registro_salud)
CATEGORIAS = [
    ('gasfiteria', 'Gasfitería', 'Filtraciones, calefont, WC, grifería y destapes.', '🔧', H, False),
    ('electricidad', 'Electricidad', 'Instalaciones, tableros, enchufes y reparaciones eléctricas.', '⚡', H, False),
    ('cerrajeria', 'Cerrajería', 'Apertura de puertas, cambio de chapas y copias de llaves.', '🔐', H, False),
    ('climatizacion', 'Climatización', 'Instalación y mantención de aire acondicionado y calefacción.', '❄️', H, False),
    ('construccion', 'Construcción', 'Obras menores, ampliaciones, remodelaciones y terminaciones.', '🏗️', H, False),
    ('limpieza', 'Limpieza', 'Aseo domiciliario, de oficinas y post obra.', '🧹', H, False),
    ('jardineria', 'Jardinería', 'Poda, riego, pasto y mantención de jardines.', '🌿', H, False),
    ('carpinteria', 'Carpintería', 'Muebles, puertas, closets y trabajos en madera.', '🪚', H, False),
    ('pintura', 'Pintura', 'Pintura interior, exterior y reparación de muros.', '🎨', H, False),

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

    ('contabilidad', 'Contabilidad y trámites', 'Inicio de actividades, contabilidad para pymes, declaraciones y trámites.', '📊', P, False),
    ('diseno-grafico', 'Diseño gráfico', 'Logos, redes sociales, material impreso e identidad de marca.', '🖌️', P, False),
    ('fotografia-y-video', 'Fotografía y video', 'Eventos, productos, retratos y contenido para redes.', '📷', P, False),
    ('soporte-computacional', 'Soporte computacional', 'Reparación de computadores, redes, respaldos y formateo.', '💻', P, False),
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
                },
            )
            creadas += int(created)
        self.stdout.write(f'Categorías: {creadas} creadas, {Category.objects.count()} en total.')
