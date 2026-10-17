from django.db import migrations

SEO = {'gasfiteria': 'Gásfiter', 'electricidad': 'Electricista', 'cerrajeria': 'Cerrajero', 'climatizacion': 'Técnico en climatización', 'construccion': 'Maestro constructor', 'limpieza': 'Servicio de aseo', 'jardineria': 'Jardinero', 'carpinteria': 'Carpintero', 'pintura': 'Pintor', 'kinesiologia': 'Kinesiólogo', 'psicologia': 'Psicólogo', 'nutricion': 'Nutricionista', 'fonoaudiologia': 'Fonoaudiólogo', 'terapia-ocupacional': 'Terapeuta ocupacional', 'enfermeria': 'Enfermería a domicilio', 'podologia': 'Podólogo', 'cuidado-de-personas': 'Cuidadora de adulto mayor', 'clases-particulares': 'Profesor particular', 'idiomas': 'Clases de inglés e idiomas', 'clases-de-musica': 'Profesor de música', 'psicopedagogia': 'Psicopedagogo', 'peluqueria': 'Peluquería a domicilio', 'manicure-y-estetica': 'Manicurista', 'contabilidad': 'Contador', 'diseno-grafico': 'Diseñador gráfico', 'fotografia-y-video': 'Fotógrafo', 'soporte-computacional': 'Técnico en computación'}


def completar(apps, schema_editor):
    Category = apps.get_model('directory', 'Category')
    for slug, nombre in SEO.items():
        Category.objects.filter(slug=slug, seo_nombre='').update(seo_nombre=nombre)


class Migration(migrations.Migration):
    dependencies = [('directory', '0011_category_seo_nombre')]
    operations = [migrations.RunPython(completar, migrations.RunPython.noop)]
