"""Clientes de GoGoDevS con perfil en ServiPlace (18-10-2026).

Cada dato sale del SITIO PÚBLICO del cliente, revisado el 18-10-2026 (los
WhatsApp, teléfonos, Instagram y correos se compararon contra el HTML de su
sitio en vivo; los dominios de correo tienen MX). Nada viene de las notas
internas: lo que el cliente no publica, no se publica aquí.

La carga la hace `manage.py cargar_clientes` (build.sh): crea los que faltan y
NUNCA pisa un perfil existente. Para corregir un dato después de cargado, se
edita en el admin o en el panel; cambiarlo aquí no actualiza nada.

VOA Chile y Travesía atienden todo Chile (lo confirmó Diego): comuna base
Santiago y "Atención en todo Chile".

Quedaron fuera por falta de un dato verificable en su sitio (18-10-2026):
Max Services (sin WhatsApp), Vizo Glow (el número no es WhatsApp en su sitio),
Punto Parcelas (sin comuna) y AZA (es una organización, no un servicio).
"""

FUENTE = 'cliente-gogodevs'

CLIENTES = [
    {
        'slug': 'gogodevs',
        'nombre': 'GoGoDevS',
        'contacto': 'Diego Dinamarca',
        'rubro': 'desarrollo-web',
        'comuna': 'santiago',
        'sector': 'Atención en todo Chile',
        'atiende': 'Todo Chile, en línea',
        'whatsapp': '56956392509',
        'telefono': '+56 9 5639 2509',
        'email': 'contacto@gogodevs.cl',
        'web': 'https://www.gogodevs.cl',
        'instagram': 'gogodevs.cl',
        'online': True,
        'corta': 'Desarrollo web en Chile: sitios, tiendas online con pago, sistemas a medida y automatización para pymes y emprendedores.',
        'larga': ('GoGoDevS hace sitios corporativos e institucionales, tiendas online con pago real, catálogo y panel '
                  'de stock y pedidos, y sistemas a medida para automatizar procesos. También SEO técnico, '
                  'integraciones de pago y apps a medida. Trabaja en cinco etapas, con capacitación y soporte los '
                  'primeros 30 días después de la entrega. Atención de lunes a viernes de 9:00 a 19:00 y sábado de '
                  '10:00 a 14:00.'),
        'fuentes': ['https://www.gogodevs.cl'],
    },
    {
        'slug': 'puas-tatuajes',
        'nombre': 'Púas Tatuajes',
        'rubro': 'tatuajes',
        'comuna': 'providencia',
        'sector': 'Las Urbinas',
        'direccion': 'Las Urbinas 30, Providencia',
        'atiende': 'En el estudio, en Providencia',
        'whatsapp': '56968195553',
        'telefono': '+56 9 6819 5553',
        'email': 'info@puastatuajes.cl',
        'web': 'https://puastatuajes.cl',
        'instagram': 'puastatuajes',
        'en_local': True,
        'corta': 'Estudio de tatuajes en Providencia desde 1992: realismo, color, fineline, polinésico y piercing.',
        'larga': ('Púas Tatuajes es un estudio de tatuajes en Providencia, activo desde 1992. Trabaja realismo, color, '
                  'fineline y polinésico, y hace piercing. Se especializa en reparar y cubrir tatuajes antiguos con '
                  'diseño polinésico. Atienden también en inglés y portugués. Horario: lunes a viernes de 11:00 a '
                  '20:00 y sábado de 11:00 a 18:00.'),
        'fuentes': ['https://puastatuajes.cl'],
    },
    {
        'slug': 'salon-amanda',
        'nombre': 'Salón Amanda',
        'rubro': 'peluqueria',
        'comuna': 'pudahuel',
        'sector': 'Ciudad de los Valles',
        'direccion': 'Av. del Canal 19926, Ciudad de los Valles, Pudahuel',
        'atiende': 'En el salón, en Ciudad de los Valles',
        'whatsapp': '56939308418',
        'telefono': '+56 9 3930 8418',
        'web': 'https://www.salonamanda.cl',
        'instagram': 'salonamanda.cl',
        'en_local': True,
        'corta': 'Salón de belleza en Ciudad de los Valles, Pudahuel: cortes, color, mechas, tratamientos, uñas y estética.',
        'larga': ('Salón Amanda atiende en Ciudad de los Valles, Pudahuel. En cabello hace cortes, brushing, peinados, '
                  'coloración, mechas, decoloración, alisados y tratamientos. En uñas, manicure, esmaltado '
                  'permanente, extensiones soft gel y acrílico, y pedicure. También perfilado de cejas, depilación '
                  'facial, lash lifting y maquillaje social. Se reserva hora en línea o por WhatsApp. Horario: lunes a '
                  'viernes de 11:00 a 21:00, sábado de 11:00 a 20:00 y domingo de 11:00 a 18:00.'),
        'fuentes': ['https://www.salonamanda.cl'],
    },
    {
        'slug': 'fco-climatizacion',
        'nombre': 'FCO Climatización',
        'rubro': 'climatizacion',
        'comuna': 'pudahuel',
        'sector': 'Ciudad de los Valles',
        'atiende': 'Pudahuel, Lampa, Quilicura, Renca, Cerro Navia, Maipú, Colina y Estación Central',
        'whatsapp': '56956393341',
        'telefono': '+56 9 5639 3341',
        'web': 'https://fcoclimatizacion.cl',
        'instagram': 'fcoclimatizacion',
        'a_domicilio': True,
        'corta': 'Instalación, mantención y reparación de aire acondicionado split para casas, oficinas y locales, con factura y garantía.',
        'larga': ('FCO Climatización instala aire acondicionado split en casas, departamentos, oficinas y locales, hace '
                  'mantención y limpieza de equipos, y repara con diagnóstico antes de cotizar. También vende equipos '
                  'y los instala. Trabaja con factura y garantía. En su sitio hay una calculadora de capacidad por '
                  'metro cuadrado; el cálculo exacto se hace en la visita técnica.'),
        'fuentes': ['https://fcoclimatizacion.cl'],
    },
    {
        'slug': 'saferoom-chile',
        'nombre': 'SafeRoom Chile',
        'rubro': 'seguridad-hogar',
        'comuna': 'santiago',
        'sector': 'Región Metropolitana',
        'atiende': 'Santiago',
        'whatsapp': '56976693158',
        'telefono': '+56 9 7669 3158',
        'web': 'https://saferoom.cl',
        'a_domicilio': True,
        'corta': 'Diseño, instalación y certificación de salas de pánico y resguardo residencial, contra asaltos y sismos.',
        'larga': ('SafeRoom Chile diseña, instala y certifica salas de resguardo para casas. El Safe Room contra '
                  'asaltos es una habitación blindada para protegerse ante robos y portonazos; el Safe Room sísmico es '
                  'una cabina de acero armable con asientos e iluminación LED. Cada módulo se diseña según el perfil '
                  'de riesgo del cliente, con comunicación al exterior y conexión con servicios de emergencia. La '
                  'asesoría es privada y confidencial, con soporte después de la instalación. Atención de lunes a '
                  'viernes de 9:00 a 19:00.'),
        'fuentes': ['https://saferoom.cl'],
    },
    {
        'slug': 'medina4x4',
        'nombre': 'Medina4x4',
        'rubro': 'repuestos-automotrices',
        'comuna': 'santiago',
        'sector': 'Santiago Centro',
        'direccion': 'Maule 1042, Santiago Centro',
        'atiende': 'Envíos a todo Chile y retiro en el local',
        'whatsapp': '56981572327',
        'telefono': '+56 2 2556 3958',
        'email': 'contacto@medina4x4.cl',
        'web': 'https://medina4x4.cl',
        'instagram': 'repuestosmedina4x4',
        'en_local': True,
        'online': True,
        'corta': 'Repuestos nuevos y alternativos para 4x4, camionetas y autos, con local en Santiago Centro y envíos a todo Chile.',
        'larga': ('Medina4x4 vende repuestos nuevos y alternativos para 4x4, camionetas y autos: diferenciales, turbos, '
                  'motores, suspensión, frenos, componentes eléctricos, dirección, climatización, combustible y '
                  'carrocería. Tiene más de 20 años de experiencia, garantía y atención personalizada, y cotiza '
                  'repuestos que no están en el catálogo. Envíos a todo Chile y retiro gratis en el local. Horario: '
                  'lunes a viernes de 9:30 a 18:00 y sábado de 9:30 a 12:30.'),
        'fuentes': ['https://medina4x4.cl'],
    },
    {
        'slug': 'comercial-villarreal',
        'nombre': 'Comercial Villarreal',
        'rubro': 'repuestos-automotrices',
        'comuna': 'santiago',
        'sector': 'Santiago Centro',
        'direccion': 'Maule 1051, Santiago',
        'atiende': 'Envíos a todo Chile y local en Santiago Centro',
        'whatsapp': '56982001138',
        'telefono': '+56 2 2551 4771',
        'email': 'contacto@villarreal.cl',
        'web': 'https://www.comercialvillarreal.cl',
        'instagram': 'comercialvillarreal',
        'en_local': True,
        'online': True,
        'corta': 'Venta e importación de repuestos automotrices multimarca, con local en Santiago Centro y envíos a todo Chile.',
        'larga': ('Comercial Villarreal vende e importa repuestos automotrices multimarca: motor, suspensión y frenos, '
                  'electrónica y encendido, carrocería, refrigeración, transmisión, dirección y combustión. Hace '
                  'envíos a todo Chile, tiene servicio de post venta y cotiza con sus expertos los repuestos que no '
                  'están publicados. Se paga con tarjeta de crédito o débito, transferencia o efectivo en el local. '
                  'Horario: lunes a viernes de 9:00 a 18:00 y sábado de 9:30 a 12:30.'),
        'fuentes': ['https://www.comercialvillarreal.cl'],
    },
    {
        'slug': 'popi-uniformes-clinicos',
        'nombre': 'Popi Uniformes Clínicos',
        'rubro': 'uniformes-y-ropa-de-trabajo',
        'comuna': 'antofagasta',
        'sector': 'Calle Maipú',
        'direccion': 'Maipú 271, Antofagasta',
        'atiende': 'Tienda en Antofagasta y envíos a todo Chile',
        'whatsapp': '56945205048',
        'telefono': '+56 9 4520 5048',
        'email': 'popiuniformesclinicos@gmail.com',
        'web': 'https://popiuniformes.cl',
        'instagram': 'popi_uniformesclinicos',
        'en_local': True,
        'online': True,
        'corta': 'Uniformes clínicos y accesorios para profesionales de la salud, con tienda en Antofagasta y envíos a todo Chile.',
        'larga': ('Popi vende uniformes clínicos de la marca Ripholia: conjuntos, chaquetas y casacas, pantalones y '
                  'delantales, en telas antifluidos, elasticadas y spandex, de la talla XXS a la XXL y en muchos '
                  'colores. También joggers, polerones, gorros, turbantes y medias compresivas. En la tienda de '
                  'Antofagasta puedes ver los colores y probarte las prendas; algunos modelos se encargan a fábrica y '
                  'la disponibilidad se confirma por WhatsApp antes de pagar.'),
        'fuentes': ['https://popiuniformes.cl'],
    },
    {
        'slug': 'ruta-motors',
        'nombre': 'Ruta Motors Chile',
        'rubro': 'automotoras',
        'comuna': 'maipu',
        'sector': 'Sucursal Maipú',
        'atiende': 'Maipú, Región Metropolitana',
        'whatsapp': '56942593560',
        'telefono': '+56 9 4259 3560',
        'web': 'https://rutamotors.onrender.com',
        'instagram': 'rutamotors.cl',
        'en_local': True,
        'corta': 'Automotora en Maipú especializada en pick-ups 4x4 y 4x2, con financiamiento y recepción de tu auto en parte de pago.',
        'larga': ('Ruta Motors Chile vende pick-ups 4x4 y 4x2, además de algunos SUV y camiones de carga, con un '
                  'catálogo acotado de vehículos revisados antes de publicarse. Ofrece financiamiento a la medida, '
                  'que se conversa por WhatsApp, y recibe tu auto como parte de pago. Acepta tarjeta de crédito y '
                  'débito. Horario: lunes a jueves de 9:30 a 17:30, viernes de 9:30 a 16:00 y sábado con previa '
                  'coordinación.'),
        'fuentes': ['https://rutamotors.onrender.com'],
    },
    {
        'slug': 'dulcecita',
        'nombre': 'Dulcecita',
        'rubro': 'reposteria-y-dulces',
        'comuna': 'santiago',
        'sector': 'Despacho a todo Chile',
        'atiende': 'Despacho a todo Chile; entrega coordinada en Santiago',
        'whatsapp': '56961192192',
        'telefono': '+56 9 6119 2192',
        'email': 'contacto@dulcecita.cl',
        'web': 'https://dulcecita.cl',
        'instagram': 'dulcecitaa.cl',
        'online': True,
        'corta': 'Repostería artesanal hecha a mano: alfajores, barquillos y cuchuflís bañados en chocolate, con box para regalar y despacho a todo Chile.',
        'larga': ('Dulcecita hace a mano alfajores, barquillos, cuchuflís, tortas de cuchuflís y otros dulces. Arma box '
                  'a pedido para empresas, fechas especiales y regalos, con empaque personalizable y tarjeta, y vende '
                  'por volumen para regalos corporativos y coffee breaks. Los pedidos parten desde 10 unidades por '
                  'producto (en "Arma tu box", desde 3) y salen 48 horas después de confirmados. Despacho a todo '
                  'Chile. Atención de lunes a sábado de 9:00 a 19:00.'),
        'fuentes': ['https://dulcecita.cl'],
    },
    {
        'slug': 'voa-chile',
        'nombre': 'VOA Chile',
        'rubro': 'traslados-y-turismo',
        'comuna': 'santiago',
        'sector': 'Atención en todo Chile',
        'atiende': 'Todo Chile; tours por la zona central',
        'whatsapp': '56945300943',
        'telefono': '+56 9 4530 0943',
        'email': 'reservas@voachile.cl',
        'web': 'https://voachile.cl',
        'instagram': 'voachile',
        'a_domicilio': True,
        'corta': 'Transporte privado y turismo en sedán, van, minibús y bus: traslados al aeropuerto, tours, matrimonios, empresas y eventos.',
        'larga': ('VOA Chile hace transporte privado y turismo con una flota de sedán (1 a 3 pasajeros), van (hasta '
                  '10), minibús (hasta 17) y bus (hasta 46). Hace traslados desde y hacia el aeropuerto, tours por la '
                  'zona central (centros de ski, Valparaíso y Viña del Mar, viñas del Maipo, Casablanca y Colchagua, '
                  'Isla Negra, Cajón del Maipo) y transporte para matrimonios, empresas, delegaciones, eventos y '
                  'producciones. Trabaja con conductores profesionales y con permisos y seguros vigentes.'),
        'fuentes': ['https://voachile.cl'],
    },
    {
        'slug': 'travesia-logistica',
        'nombre': 'Travesía Logística',
        'rubro': 'fletes-y-logistica',
        'comuna': 'santiago',
        'sector': 'Atención en todo Chile',
        'atiende': 'De Arica a Punta Arenas, con rutas a Argentina, Brasil y Paraguay',
        'whatsapp': '56923763329',
        'telefono': '+56 9 2376 3329',
        'web': 'https://travesialogistica.cl',
        'corta': 'Transporte y logística para empresas, nacional e internacional: logística minera, cargas especiales y arriendo de equipos para faenas.',
        'larga': ('Travesía Logística hace transporte nacional e internacional para empresas, logística minera y '
                  'soporte logístico para obras y faenas. Mueve cargas especiales, refrigeradas, peligrosas y de '
                  'sobredimensión, asesora en comercio exterior y proyectos logísticos, y arrienda equipos con o sin '
                  'operador: camionetas, camión 3/4, camión de combustible, aljibes, tolvas, camión pluma, '
                  'retroexcavadora, excavadora y tracto camión con rampla y cama baja. Cubre de Arica a Punta Arenas, '
                  'con rutas a Argentina, Brasil y Paraguay.'),
        'fuentes': ['https://travesialogistica.cl', 'https://travesialogistica.cl/contacto/'],
    },
]
