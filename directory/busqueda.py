"""La búsqueda entiende oficios (20-10-2026).

La gente escribe "fotógrafo", "diseñador", "gasfiter" o "abogado"; los rubros
se llaman "Fotografía y video", "Diseño gráfico", "Gasfitería", "Asesoría
legal". La búsqueda comparaba la palabra con el NOMBRE del rubro y con tildes
exactas: "fotógrafo" daba cero aunque hubiera fotógrafos publicados. Acá cada
rubro tiene su nombre, su nombre de búsqueda (seo_nombre) y sinónimos, y se
compara todo sin tildes, en minúsculas y aceptando plurales.
"""
import re
import unicodedata

from .models import Category

SINONIMOS = {
    'gasfiteria': ['gasfiter', 'plomero', 'destape', 'calefont'],
    'electricidad': ['electricista', 'electrico'],
    'cerrajeria': ['cerrajero', 'llaves'],
    'climatizacion': ['aire acondicionado', 'refrigeracion', 'calefaccion'],
    'construccion': ['constructor', 'albanil', 'maestro', 'remodelacion', 'ampliacion'],
    'soldadura': ['soldador', 'reja', 'porton'],
    'carpinteria': ['carpintero', 'mueblista', 'mueble'],
    'pintura': ['pintor'],
    'jardineria': ['jardinero', 'paisajista'],
    'limpieza': ['aseo'],
    'seguridad-hogar': ['alarma', 'camaras'],
    'mecanica-automotriz': ['mecanico', 'auto', 'taller mecanico'],
    'kinesiologia': ['kinesiologo', 'kine'],
    'psicologia': ['psicologo', 'terapia'],
    'nutricion': ['nutricionista'],
    'fonoaudiologia': ['fonoaudiologo', 'fono'],
    'podologia': ['podologo'],
    'enfermeria': ['enfermera', 'enfermero', 'tens'],
    'cuidado-de-personas': ['cuidadora', 'adulto mayor'],
    'entrenamiento-personal': ['entrenador', 'personal trainer', 'preparador fisico'],
    'clases-particulares': ['profesor', 'profe', 'clases', 'reforzamiento'],
    'idiomas': ['ingles', 'idioma'],
    'clases-de-musica': ['guitarra', 'piano', 'musica'],
    'peluqueria': ['peluquero', 'peluquera', 'barbero'],
    'manicure-y-estetica': ['manicurista', 'unas'],
    'tatuajes': ['tatuador', 'tattoo'],
    'contabilidad': ['contador', 'contadora', 'impuestos'],
    'diseno-grafico': ['disenador', 'disenadora', 'logo'],
    'fotografia-y-video': ['fotografo', 'fotografa', 'camarografo', 'videografo'],
    'soporte-computacional': ['informatico', 'informatica', 'computador', 'notebook'],
    'desarrollo-web': ['informatico', 'informatica', 'programador', 'pagina web', 'sitio web', 'software'],
    'edicion-de-video': ['editor', 'editora', 'edicion'],
    'marketing-y-rrpp': ['marketing', 'community manager', 'redes sociales', 'relaciones publicas', 'rrpp', 'publicidad'],
    'produccion-de-eventos': ['eventos', 'matrimonio', 'cumpleanos', 'wedding planner'],
    'asesoria-legal': ['abogado', 'abogada', 'legal', 'juridico'],
    'arquitectura': ['arquitecto', 'arquitecta', 'planos', 'regularizacion'],
    'traduccion': ['traductor', 'traductora'],
    'fletes-y-logistica': ['flete', 'mudanza'],
    'traslados-y-turismo': ['traslado', 'transfer', 'aeropuerto'],
    'reposteria-y-dulces': ['torta', 'pasteleria'],
}


def normalizar(texto):
    """Minúsculas, sin tildes ni signos: "Fotógrafa!" -> "fotografa"."""
    plano = unicodedata.normalize('NFKD', (texto or '').lower())
    plano = ''.join(c for c in plano if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', plano))


def _calza(busqueda, palabras, clave):
    # La clave entera dentro de la búsqueda: "busco editor de video".
    if re.search(rf'\b{re.escape(clave)}\b', busqueda):
        return True
    for p in palabras:
        if len(p) < 4:
            continue
        for w in clave.split():
            # "diseno" -> "diseno grafico"; "fotografos" -> "fotografo".
            if w.startswith(p) or (len(w) >= 5 and p.startswith(w)):
                return True
    return False


def rubros_de_la_busqueda(texto):
    """Los ids de los rubros que nombra la búsqueda (una consulta: son ~45)."""
    busqueda = normalizar(texto)
    if len(busqueda) < 3:
        return []
    palabras = busqueda.split()
    ids = []
    for c in Category.objects.filter(is_active=True).only('pk', 'slug', 'name', 'seo_nombre'):
        claves = [normalizar(c.name), normalizar(c.seo_nombre)] + [normalizar(s) for s in SINONIMOS.get(c.slug, ())]
        if any(clave and _calza(busqueda, palabras, clave) for clave in claves):
            ids.append(c.pk)
    return ids
