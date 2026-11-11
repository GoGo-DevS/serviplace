"""Procesa el logo o la foto que sube un profesional.

Regla 12 de GoGoDevS: la imagen se guarda ya achicada (WebP de menos de
100 KB). Además se corrige la rotación de las fotos de celular y se descarta
el EXIF: una foto tomada en la casa puede traer su ubicación GPS, y esa foto
queda pública.
"""
import io
import uuid

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

LADO_MAXIMO = 640
PESO_MAXIMO = 100 * 1024
SUBIDA_MAXIMA = 8 * 1024 * 1024
FORMATOS = {'JPEG', 'PNG', 'WEBP', 'GIF', 'MPO'}


def procesar_foto(archivo, lado_maximo=LADO_MAXIMO):
    """Devuelve un ContentFile WebP listo para guardar, o lanza ValidationError.
    El logo va a 640 px; las fotos de trabajos, a 1024."""
    if archivo.size > SUBIDA_MAXIMA:
        raise ValidationError('La imagen pesa más de 8 MB. Prueba con otra o recórtala.')
    try:
        imagen = Image.open(archivo)
        formato = imagen.format
        if formato not in FORMATOS:
            raise ValidationError('Usa una imagen JPG, PNG o WebP.')
        # 11-11-2026: guardar el perfil daba 502 en Render (plan gratis, una
        # décima de CPU, 30 s por petición). Decodificar la foto completa del
        # celular (12 MP) tomaba ~1,2 s por foto en un PC y ~10 veces más allá.
        # draft le pide al JPEG que se decodifique ya reducido (1/2, 1/4 o 1/8),
        # nunca por debajo del doble del lado final: misma calidad, mucho menos
        # trabajo y memoria. En PNG y WebP no hace nada.
        imagen.draft(imagen.mode, (lado_maximo * 2, lado_maximo * 2))
        imagen.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValidationError('No pudimos leer ese archivo como imagen. Usa JPG, PNG o WebP.')

    imagen = ImageOps.exif_transpose(imagen)  # la foto del celular, derecha
    imagen = imagen.convert('RGBA' if imagen.mode in ('RGBA', 'LA', 'P') else 'RGB')
    imagen.thumbnail((lado_maximo, lado_maximo), Image.LANCZOS, reducing_gap=3.0)

    # method=4 (el normal) en vez de 6: casi el mismo peso y varias veces más
    # rápido. Y dos intentos de calidad en vez de cuatro: cada uno es una
    # codificación completa.
    for calidad in (80, 60):
        salida = io.BytesIO()
        imagen.save(salida, 'WEBP', quality=calidad, method=4)  # sin exif=: no se copia
        if salida.tell() <= PESO_MAXIMO:
            break
    else:
        imagen.thumbnail((lado_maximo // 2, lado_maximo // 2), Image.LANCZOS)
        salida = io.BytesIO()
        imagen.save(salida, 'WEBP', quality=60, method=4)

    return ContentFile(salida.getvalue(), name=f'{uuid.uuid4().hex[:16]}.webp')
