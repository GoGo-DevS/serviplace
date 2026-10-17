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


def procesar_foto(archivo):
    """Devuelve un ContentFile WebP listo para guardar, o lanza ValidationError."""
    if archivo.size > SUBIDA_MAXIMA:
        raise ValidationError('La imagen pesa más de 8 MB. Prueba con otra o recórtala.')
    try:
        imagen = Image.open(archivo)
        formato = imagen.format
        imagen.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValidationError('No pudimos leer ese archivo como imagen. Usa JPG, PNG o WebP.')
    if formato not in FORMATOS:
        raise ValidationError('Usa una imagen JPG, PNG o WebP.')

    imagen = ImageOps.exif_transpose(imagen)  # la foto del celular, derecha
    imagen = imagen.convert('RGBA' if imagen.mode in ('RGBA', 'LA', 'P') else 'RGB')
    imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO), Image.LANCZOS)

    for calidad in (82, 72, 62, 52):
        salida = io.BytesIO()
        imagen.save(salida, 'WEBP', quality=calidad, method=6)  # sin exif=: no se copia
        if salida.tell() <= PESO_MAXIMO:
            break
    else:
        imagen.thumbnail((LADO_MAXIMO // 2, LADO_MAXIMO // 2), Image.LANCZOS)
        salida = io.BytesIO()
        imagen.save(salida, 'WEBP', quality=60, method=6)

    return ContentFile(salida.getvalue(), name=f'{uuid.uuid4().hex[:16]}.webp')
