from django.core.management.base import BaseCommand
from django.utils.text import slugify

from directory.models import Commune, Region

REGIONES_COMUNAS = [
    {
        'name': 'Región de Arica y Parinacota',
        'comunas': ['Arica', 'Camarones', 'General Lagos', 'Putre'],
    },
    {
        'name': 'Región de Tarapacá',
        'comunas': ['Alto Hospicio', 'Camiña', 'Colchane', 'Huara', 'Iquique', 'Pica', 'Pozo Almonte'],
    },
    {
        'name': 'Región de Antofagasta',
        'comunas': [
            'Antofagasta', 'Calama', 'María Elena', 'Mejillones', 'Ollagüe',
            'San Pedro de Atacama', 'Sierra Gorda', 'Taltal', 'Tocopilla',
        ],
    },
    {
        'name': 'Región de Atacama',
        'comunas': [
            'Alto del Carmen', 'Caldera', 'Chañaral', 'Copiapó', 'Diego de Almagro',
            'Freirina', 'Huasco', 'Tierra Amarilla', 'Vallenar',
        ],
    },
    {
        'name': 'Región de Coquimbo',
        'comunas': [
            'Andacollo', 'Canela', 'Combarbalá', 'Coquimbo', 'Illapel',
            'La Higuera', 'La Serena', 'Los Vilos', 'Monte Patria', 'Ovalle',
            'Paiguano', 'Punitaqui', 'Río Hurtado', 'Salamanca', 'Vicuña',
        ],
    },
    {
        'name': 'Región de Valparaíso',
        'comunas': [
            'Algarrobo', 'Cabildo', 'Calera', 'Calle Larga', 'Cartagena',
            'Casablanca', 'Catemu', 'Concón', 'El Quisco', 'El Tabo',
            'Hijuelas', 'Isla de Pascua', 'Juan Fernández', 'La Cruz', 'La Ligua',
            'Limache', 'Llaillay', 'Los Andes', 'Nogales', 'Olmué',
            'Panquehue', 'Papudo', 'Petorca', 'Puchuncaví', 'Putaendo',
            'Quillota', 'Quilpué', 'Quintero', 'Rinconada', 'San Antonio',
            'San Esteban', 'San Felipe', 'Santa María', 'Santo Domingo',
            'Valparaíso', 'Villa Alemana', 'Viña del Mar', 'Zapallar',
        ],
    },
    {
        'name': "Región del Libertador General Bernardo O'Higgins",
        'comunas': [
            'Chimbarongo', 'Chépica', 'Codegua', 'Coinco', 'Coltauco',
            'Doñihue', 'Graneros', 'La Estrella', 'Las Cabras', 'Litueche',
            'Lolol', 'Machalí', 'Malloa', 'Marchigüe', 'Mostazal',
            'Nancagua', 'Navidad', 'Olivar', 'Palmilla', 'Paredones',
            'Peralillo', 'Peumo', 'Pichidegua', 'Pichilemu', 'Placilla',
            'Pumanque', 'Quinta de Tilcoco', 'Rancagua', 'Rengo', 'Requínoa',
            'San Fernando', 'San Vicente', 'Santa Cruz',
        ],
    },
    {
        'name': 'Región del Maule',
        'comunas': [
            'Cauquenes', 'Chanco', 'Colbún', 'Constitución', 'Curepto',
            'Curicó', 'Empedrado', 'Hualañé', 'Licantén', 'Linares',
            'Longaví', 'Maule', 'Molina', 'Parral', 'Pelarco',
            'Pelluhue', 'Pencahue', 'Rauco', 'Retiro', 'Río Claro',
            'Romeral', 'Sagrada Familia', 'San Clemente', 'San Javier', 'San Rafael',
            'Talca', 'Teno', 'Vichuquén', 'Villa Alegre', 'Yerbas Buenas',
        ],
    },
    {
        'name': 'Región de Ñuble',
        'comunas': [
            'Bulnes', 'Chillán', 'Chillán Viejo', 'Cobquecura', 'Coelemu',
            'Coihueco', 'El Carmen', 'Ninhue', 'Ñiquén', 'Pemuco',
            'Pinto', 'Portezuelo', 'Quillón', 'Quirihue', 'Ránquil',
            'San Carlos', 'San Fabián', 'San Ignacio', 'San Nicolás', 'Trehuaco',
            'Yungay',
        ],
    },
    {
        'name': 'Región del Biobío',
        'comunas': [
            'Alto Biobío', 'Antuco', 'Arauco', 'Cabrero', 'Cañete',
            'Chiguayante', 'Concepción', 'Contulmo', 'Coronel', 'Curanilahue',
            'Florida', 'Hualpén', 'Hualqui', 'Laja', 'Lebu',
            'Los Álamos', 'Los Ángeles', 'Lota', 'Mulchén', 'Nacimiento',
            'Negrete', 'Penco', 'Quilaco', 'Quilleco', 'San Pedro de la Paz',
            'San Rosendo', 'Santa Bárbara', 'Santa Juana', 'Talcahuano', 'Tirúa',
            'Tomé', 'Tucapel', 'Yumbel',
        ],
    },
    {
        'name': 'Región de La Araucanía',
        'comunas': [
            'Angol', 'Carahue', 'Cholchol', 'Collipulli', 'Cunco',
            'Curacautín', 'Curarrehue', 'Ercilla', 'Freire', 'Galvarino',
            'Gorbea', 'Lautaro', 'Loncoche', 'Lonquimay', 'Los Sauces',
            'Lumaco', 'Melipeuco', 'Nueva Imperial', 'Padre Las Casas', 'Perquenco',
            'Pitrufquén', 'Pucón', 'Purén', 'Renaico', 'Saavedra',
            'Temuco', 'Teodoro Schmidt', 'Toltén', 'Traiguén', 'Victoria',
            'Vilcún', 'Villarrica',
        ],
    },
    {
        'name': 'Región de Los Ríos',
        'comunas': [
            'Corral', 'Futrono', 'La Unión', 'Lago Ranco', 'Lanco',
            'Los Lagos', 'Máfil', 'Mariquina', 'Paillaco', 'Panguipulli',
            'Río Bueno', 'Valdivia',
        ],
    },
    {
        'name': 'Región de Los Lagos',
        'comunas': [
            'Ancud', 'Calbuco', 'Castro', 'Chaitén', 'Chonchi',
            'Cochamó', 'Curaco de Vélez', 'Dalcahue', 'Fresia', 'Frutillar',
            'Futaleufú', 'Hualaihué', 'Llanquihue', 'Los Muermos', 'Maullín',
            'Osorno', 'Palena', 'Puerto Montt', 'Puerto Octay', 'Puerto Varas',
            'Puqueldón', 'Purranque', 'Puyehue', 'Queilén', 'Quellón',
            'Quemchi', 'Quinchao', 'Río Negro', 'San Juan de la Costa', 'San Pablo',
        ],
    },
    {
        'name': 'Región de Aysén del General Carlos Ibáñez del Campo',
        'comunas': [
            'Aysén', 'Chile Chico', 'Cisnes', 'Cochrane', 'Coyhaique',
            "Guaitecas", 'Lago Verde', "O'Higgins", 'Río Ibáñez', 'Tortel',
        ],
    },
    {
        'name': 'Región de Magallanes y de la Antártica Chilena',
        'comunas': [
            'Antártica', 'Cabo de Hornos', 'Laguna Blanca', 'Natales', 'Porvenir',
            'Primavera', 'Punta Arenas', 'Río Verde', 'San Gregorio', 'Timaukel',
            'Torres del Paine',
        ],
    },
    {
        'name': 'Región Metropolitana de Santiago',
        'comunas': [
            # Provincia de Santiago
            'Cerrillos', 'Cerro Navia', 'Conchalí', 'El Bosque', 'Estación Central',
            'Huechuraba', 'Independencia', 'La Cisterna', 'La Florida', 'La Granja',
            'La Pintana', 'La Reina', 'Las Condes', 'Lo Barnechea', 'Lo Espejo',
            'Lo Prado', 'Macul', 'Maipú', 'Ñuñoa', 'Pedro Aguirre Cerda',
            'Peñalolén', 'Providencia', 'Pudahuel', 'Quilicura', 'Quinta Normal',
            'Recoleta', 'Renca', 'San Joaquín', 'San Miguel', 'San Ramón',
            'Santiago', 'Vitacura',
            # Provincia Cordillera
            'Pirque', 'Puente Alto', 'San José de Maipo',
            # Provincia Chacabuco
            'Colina', 'Lampa', 'Tiltil',
            # Provincia Maipo
            'Buin', 'Calera de Tango', 'Paine', 'San Bernardo',
            # Provincia Melipilla
            'Alhué', 'Curacaví', 'María Pinto', 'Melipilla', 'San Pedro',
            # Provincia Talagante
            'El Monte', 'Isla de Maipo', 'Padre Hurtado', 'Peñaflor', 'Talagante',
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed de las 16 regiones y 346 comunas de Chile (INE/SUBDERE). Idempotente.'

    def handle(self, *args, **options):
        total_regiones = 0
        total_comunas = 0
        nuevas_comunas = 0
        nuevas_regiones = 0

        for datos in REGIONES_COMUNAS:
            region, creada = Region.objects.get_or_create(
                name=datos['name'],
                defaults={'slug': slugify(datos['name']), 'is_active': True},
            )
            if creada:
                nuevas_regiones += 1
                self.stdout.write(self.style.SUCCESS(f'  + Región: {region.name}'))
            else:
                self.stdout.write(f'  = Región: {region.name}')
            total_regiones += 1

            for nombre_comuna in datos['comunas']:
                slug_comuna = slugify(nombre_comuna)
                comuna, creada_c = Commune.objects.get_or_create(
                    slug=slug_comuna,
                    defaults={'name': nombre_comuna, 'region': region, 'is_active': True},
                )
                if not creada_c and comuna.region != region:
                    # Corrige si la región cambió (edge case: Maipú ya existía sin región)
                    Commune.objects.filter(pk=comuna.pk).update(region=region)
                    self.stdout.write(self.style.WARNING(f'    ~ Región corregida: {nombre_comuna}'))
                if creada_c:
                    nuevas_comunas += 1
                total_comunas += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Listo. {total_regiones} regiones ({nuevas_regiones} nuevas), '
            f'{total_comunas} comunas ({nuevas_comunas} nuevas).'
        ))
