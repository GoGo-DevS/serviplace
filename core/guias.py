"""Guías de /guias/ (18-10-2026).

Contenido que posiciona HOY, sin depender de cuántos perfiles hay publicados:
preguntas literales que la gente le hace a Google (y a las IAs) antes de
contratar o al empezar a trabajar por su cuenta. Dos públicos:
  - vecinos: cómo verificar a quien van a contratar (confianza);
  - profesionales: boleta, inicio de actividades, primeros clientes.

El cuerpo de cada guía vive en templates/guias/<slug>.html. Los datos legales
están verificados contra fuentes oficiales (SII, ChileAtiende, Superintendencia
de Salud, SEC) el 18-10-2026; las fuentes van citadas al final de cada guía.
Al cambiar un dato, actualizar `actualizada`.
"""
from datetime import date

GUIAS = [
    {
        'slug': 'verificar-registro-profesional-de-salud',
        'publico': 'vecinos',
        'titulo': 'Cómo verificar si un profesional de la salud está registrado',
        'title': 'Verificar el registro de un profesional de salud',
        'meta': 'Paso a paso para comprobar en el registro de la Superintendencia de Salud que un kinesiólogo, psicólogo, nutricionista o enfermera tiene su título.',
        'resumen': 'En Chile, los profesionales de la salud aparecen en un registro público y gratuito de la Superintendencia de Salud. Se consulta con el nombre o el RUT y toma un minuto.',
        'rubros': ['kinesiologia', 'psicologia', 'nutricion', 'fonoaudiologia', 'terapia-ocupacional', 'enfermeria', 'podologia'],
        'publicada': date(2026, 10, 18),
        'actualizada': date(2026, 10, 18),
    },
    {
        'slug': 'verificar-instalador-sec',
        'publico': 'vecinos',
        'titulo': 'Cómo saber si un electricista o un gásfiter está autorizado por la SEC',
        'title': 'Saber si un instalador está autorizado por la SEC',
        'meta': 'Qué es la licencia SEC, qué clases existen para electricidad y gas, y cómo usar el buscador oficial de instaladores autorizados antes de contratar.',
        'resumen': 'Los trabajos de gas y las instalaciones eléctricas los debe hacer un instalador autorizado por la Superintendencia de Electricidad y Combustibles (SEC). La SEC tiene un buscador público de instaladores vigentes.',
        'rubros': ['electricidad', 'gasfiteria', 'climatizacion'],
        'publicada': date(2026, 10, 18),
        'actualizada': date(2026, 10, 18),
    },
    {
        'slug': 'antes-de-contratar-un-maestro',
        'publico': 'vecinos',
        'titulo': 'Antes de contratar a un maestro: lo que conviene acordar',
        'title': 'Antes de contratar a un maestro: qué acordar',
        'meta': 'Checklist para contratar a un gásfiter, electricista, pintor o maestro constructor sin sorpresas: presupuesto por escrito, plazos, materiales, pagos y garantía.',
        'resumen': 'La mayoría de los problemas con un trabajo en la casa no vienen de un mal maestro, sino de algo que nadie dejó por escrito. Esta lista te ayuda a acordarlo antes de partir.',
        'rubros': ['gasfiteria', 'electricidad', 'construccion', 'pintura', 'carpinteria', 'climatizacion'],
        'publicada': date(2026, 10, 18),
        'actualizada': date(2026, 10, 18),
    },
    {
        'slug': 'boleta-de-honorarios',
        'publico': 'profesionales',
        'titulo': 'Boleta de honorarios 2026: cómo emitirla y cuánto se retiene',
        'title': 'Boleta de honorarios 2026: emisión y retención',
        'meta': 'Cómo emitir una boleta de honorarios electrónica en el SII, por qué en 2026 se retiene el 15,25% y qué pasa cuando tu cliente es una persona y no una empresa.',
        'resumen': 'Si trabajas por tu cuenta, la boleta de honorarios se emite gratis en el sitio del SII. En 2026 la retención es de 15,25%, y quién la paga depende de si tu cliente es una empresa o una persona.',
        'rubros': [],
        'publicada': date(2026, 10, 18),
        'actualizada': date(2026, 10, 18),
    },
    {
        'slug': 'inicio-de-actividades-sii',
        'publico': 'profesionales',
        'titulo': 'Inicio de actividades en el SII para trabajar como independiente',
        'title': 'Inicio de actividades en el SII como independiente',
        'meta': 'Qué es el inicio de actividades, por qué lo necesitas para emitir boletas de honorarios y cómo hacerlo en línea en el SII con tu Clave Tributaria o ClaveÚnica.',
        'resumen': 'Para emitir boletas de honorarios electrónicas necesitas haber dado aviso de inicio de actividades en el SII, en segunda categoría. Es un trámite en línea.',
        'rubros': [],
        'publicada': date(2026, 10, 18),
        'actualizada': date(2026, 10, 18),
    },
    {
        'slug': 'primeros-clientes-independiente',
        'publico': 'profesionales',
        'titulo': 'Cómo conseguir tus primeros clientes como profesional independiente',
        'title': 'Primeros clientes como profesional independiente',
        'meta': 'Lo que funciona cuando recién empiezas por tu cuenta: tu red cercana, un link profesional para compartir, aparecer en tu comuna y pedir recomendaciones.',
        'resumen': 'Los primeros clientes casi nunca llegan por publicidad: llegan por gente que ya te conoce y por quien te encuentra cerca. Esta guía ordena lo que sirve en las primeras semanas.',
        'rubros': [],
        'publicada': date(2026, 10, 18),
        'actualizada': date(2026, 10, 18),
    },
]

POR_SLUG = {g['slug']: g for g in GUIAS}


def para_rubro(rubro):
    """Guías que conviene enlazar desde una especialidad."""
    return [g for g in GUIAS if rubro in g['rubros']]


def de_profesionales():
    return [g for g in GUIAS if g['publico'] == 'profesionales']
