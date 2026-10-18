import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils import timezone
from django.utils.html import strip_tags

from django.core.files.uploadedfile import UploadedFile

from accounts.cv import ACEPTA, CVIlegible, extraer_texto
from core.antispam import AntispamFormMixin
from directory.imagenes import procesar_foto
from directory.models import Category, Commune, Provider, ProviderImage

MAX_FOTOS = 8


class VariasFotosInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class VariasFotosField(forms.FileField):
    """Un <input type=file multiple>: devuelve una lista (patrón de la doc de Django)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', VariasFotosInput(attrs={'accept': 'image/jpeg,image/png,image/webp',
                                                            'multiple': True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        uno = super().clean
        if isinstance(data, (list, tuple)):
            return [uno(d, initial) for d in data if d]
        return [uno(data, initial)] if data else []

User = get_user_model()

_CONTROL_CHARS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def limpiar_texto(valor, permitir_saltos=False):
    """Sin etiquetas HTML ni caracteres de control. El escape al mostrar lo hace Django."""
    if not valor:
        return valor
    valor = strip_tags(str(valor))
    valor = _CONTROL_CHARS.sub('', valor)
    if not permitir_saltos:
        valor = ' '.join(valor.split())
    return valor.strip()


def normalizar_movil(valor):
    """Devuelve dígitos 569XXXXXXXX o '' si no es un móvil chileno."""
    digitos = ''.join(ch for ch in (valor or '') if ch.isdigit())
    if len(digitos) == 9 and digitos.startswith('9'):
        digitos = '56' + digitos
    if len(digitos) == 11 and digitos.startswith('569'):
        return digitos
    return ''


def formatear_telefono(valor):
    digitos = ''.join(ch for ch in (valor or '') if ch.isdigit())
    if len(digitos) == 9 and digitos[0] in '92':
        digitos = '56' + digitos
    if len(digitos) == 11 and digitos.startswith('56'):
        return f'+56 {digitos[2]} {digitos[3:7]} {digitos[7:]}'
    return limpiar_texto(valor)


class LoginForm(AuthenticationForm):
    """El formulario de Django tal cual no trae las clases del sitio: los campos
    salían con el estilo del navegador y la etiqueta pegada al lado."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['password'].label = 'Contraseña'
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'current-password'})


class RegisterForm(AntispamFormMixin, UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    whatsapp = forms.CharField(
        max_length=30,
        required=False,
        label='WhatsApp (opcional)',
        help_text='Ej: +56 9 1234 5678',
    )
    cv = forms.FileField(
        required=False,
        label='Tu CV (opcional)',
        help_text='PDF o Word. Lo leemos para llenarte el perfil y no lo guardamos.',
        widget=forms.FileInput(attrs={'accept': ACEPTA}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['username'].help_text = 'Solo letras, números y @/./+/-/_'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password1'].help_text = 'Mínimo 8 caracteres. No uses solo números.'
        self.fields['password2'].label = 'Confirmar contraseña'
        self.fields['password2'].help_text = ''
        # Lo que se leyó del CV, o por qué no se pudo. Un CV ilegible NO
        # impide crear la cuenta: es opcional, y el navegador obligaría a
        # reescribir las contraseñas por un archivo que no hacía falta.
        self.cv_texto, self.cv_error = '', ''
        for name, field in self.fields.items():
            if name.startswith('sitio_web') or name.startswith('sello_'):
                continue
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs.setdefault('autocomplete', 'off' if 'password' in name else 'on')

    def clean_whatsapp(self):
        valor = self.cleaned_data.get('whatsapp', '')
        if valor and not normalizar_movil(valor):
            raise forms.ValidationError('Escribe un celular chileno: +56 9 XXXX XXXX.')
        return normalizar_movil(valor)

    def clean_cv(self):
        archivo = self.cleaned_data.get('cv')
        if archivo:
            try:
                self.cv_texto = extraer_texto(archivo)
            except CVIlegible as error:
                self.cv_error = str(error)
        return None  # el archivo no sigue viaje: ni al usuario ni a la sesión

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo. ¿Quieres iniciar sesión?')
        return email

    def antispam_textos(self):
        return [self.data.get('username', ''), self.data.get('email', '')]


class ProviderForm(AntispamFormMixin, forms.ModelForm):
    # 18-10-2026: la ficha decía "Todavía no subes fotos. Agregar fotos →" y el
    # formulario solo tenía el logo: no había dónde subir los trabajos.
    fotos = VariasFotosField(
        required=False, label='Agregar fotos',
        help_text=f'Hasta {MAX_FOTOS}. JPG, PNG o WebP; las achicamos y les quitamos la ubicación del celular.',
    )

    class Meta:
        model = Provider
        fields = [
            'business_name',
            'contact_name',
            'category',
            'commune',
            'sector',
            'foto',
            'short_description',
            'description',
            'phone',
            'whatsapp_number',
            'email',
            'website',
            'instagram',
            'address',
            'service_area',
            'attends_home',
            'attends_office',
            'attends_online',
            'profession_title',
            'institution',
            'graduation_year',
            'health_registry',
        ]
        labels = {
            'business_name': 'Nombre con el que te presentas',
            'contact_name': 'Tu nombre',
            'category': 'Rubro',
            'commune': 'Comuna base',
            'sector': 'Sector o barrio',
            'short_description': 'En una frase, qué haces',
            'description': 'Cuéntale al vecino qué haces y cómo trabajas',
            'phone': 'Teléfono',
            'whatsapp_number': 'WhatsApp',
            'email': 'Correo (opcional)',
            'website': 'Sitio web (opcional)',
            'instagram': 'Instagram (opcional)',
            'address': 'Dirección (opcional)',
            'service_area': 'Dónde atiendes (opcional)',
            'foto': 'Tu logo o una foto tuya',
            'attends_home': 'A domicilio',
            'attends_office': 'En consulta o local',
            'attends_online': 'Online',
            'profession_title': 'Título o profesión',
            'institution': 'Dónde estudiaste',
            'graduation_year': 'Año de titulación',
            'health_registry': 'N° de registro en la Superintendencia de Salud',
        }
        help_texts = {
            'short_description': 'Máximo 220 caracteres. Es lo que se ve en la tarjeta.',
            'whatsapp_number': 'Celular chileno. Es el botón principal de tu perfil.',
            'service_area': 'Ej: Maipú, Cerrillos y Pudahuel',
            'instagram': 'Tu usuario, con o sin @. Sirve como portafolio.',
            'foto': 'JPG, PNG o WebP. La achicamos y le quitamos los datos de ubicación del celular.',
            'profession_title': 'Tu título, oficio o certificación.',
            'business_name': 'Tu negocio o tu nombre profesional. Ej: Camila Rojas Kinesiología, Gasfitería Pérez.',
            'institution': 'Ej: Universidad de Concepción, INACAP, Duoc UC.',
            'graduation_year': 'Si todavía estudias, el año en que te titulas.',
            'health_registry': 'Solo si eres profesional de la salud. Tus pacientes pueden comprobarlo en el registro público.',
        }
        error_messages = {
            'foto': {'invalid_image': 'No pudimos leer ese archivo como imagen. Usa JPG, PNG o WebP.'},
        }
        widgets = {
            'short_description': forms.TextInput(attrs={'maxlength': 220, 'placeholder': 'Ej: Kinesióloga a domicilio, rehabilitación y adulto mayor'}),
            'description': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Qué haces, cómo trabajas, horarios, valores de referencia, si entregas boleta…'}),
            'foto': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
            'profession_title': forms.TextInput(attrs={'placeholder': 'Ej: Kinesióloga'}),
            'institution': forms.TextInput(attrs={'placeholder': 'Ej: Universidad de Concepción'}),
            'graduation_year': forms.NumberInput(attrs={'placeholder': 'Ej: 2025', 'inputmode': 'numeric'}),
            'health_registry': forms.TextInput(attrs={'placeholder': 'Ej: 654321', 'inputmode': 'numeric'}),
            'sector': forms.TextInput(attrs={'placeholder': 'Ej: Ciudad Satélite'}),
            'phone': forms.TextInput(attrs={'placeholder': '+56 9 1234 5678', 'inputmode': 'tel'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://tusitio.cl', 'inputmode': 'url'}),
            'instagram': forms.TextInput(attrs={'placeholder': 'tu.usuario', 'autocapitalize': 'none', 'spellcheck': 'false'}),
            'whatsapp_number': forms.TextInput(attrs={'placeholder': '+56 9 1234 5678', 'inputmode': 'tel'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Para borrar la foto anterior si la reemplaza o la quita.
        self._foto_anterior = self.instance.foto.name if self.instance.pk and self.instance.foto else ''
        self.fields['website'].assume_scheme = 'https'  # "tusitio.cl" -> https://, no http://
        # Se puede pegar el enlace completo de Instagram: el tope de 30 es del
        # usuario que se guarda (lo valida el modelo), no de lo que se escribe.
        instagram = self.fields['instagram']
        instagram.max_length, instagram.validators = 200, []
        instagram.widget.attrs['maxlength'] = 200
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['commune'].queryset = Commune.objects.filter(is_active=True).select_related('region').order_by('name')
        self.fields['category'].empty_label = 'Elige un rubro'
        self.fields['commune'].empty_label = 'Elige tu comuna'
        # 27 rubros en una lista plana no se leen: se agrupan como en la
        # portada. La validación sigue siendo la del queryset (por pk).
        categorias = list(self.fields['category'].queryset)
        # Para que el formulario se adapte al rubro elegido (18-10-2026: a un
        # ingeniero en informática le pedía el registro de la Superintendencia
        # de Salud y le daba "Kinesióloga" de ejemplo).
        self.categorias_info = {str(c.pk): {'salud': c.pide_registro_salud, 'grupo': c.group} for c in categorias}
        nombres = dict(Category.GROUP_CHOICES)
        self.fields['category'].choices = [('', 'Elige un rubro')] + [
            (nombres[clave], [(c.pk, c.name) for c in categorias if c.group == clave])
            for clave, _, _ in Category.GRUPOS
            if any(c.group == clave for c in categorias)
        ]
        self.fields['category'].label = 'Rubro o especialidad'
        for name, field in self.fields.items():
            if name.startswith('sitio_web') or name.startswith('sello_'):
                continue
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{css} form-check-input'.strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = f'{css} form-select'.strip()
            else:
                field.widget.attrs['class'] = f'{css} form-control'.strip()

    # Sanitización: se guarda texto plano. Django escapa al mostrar.
    def clean_business_name(self):
        return limpiar_texto(self.cleaned_data['business_name'])

    def clean_contact_name(self):
        return limpiar_texto(self.cleaned_data['contact_name'])

    def clean_sector(self):
        return limpiar_texto(self.cleaned_data['sector'])

    def clean_short_description(self):
        return limpiar_texto(self.cleaned_data['short_description'])[:220]

    def clean_description(self):
        return limpiar_texto(self.cleaned_data['description'], permitir_saltos=True)

    def clean_address(self):
        return limpiar_texto(self.cleaned_data.get('address', ''))

    def clean_service_area(self):
        return limpiar_texto(self.cleaned_data.get('service_area', ''))

    def clean_phone(self):
        valor = formatear_telefono(self.cleaned_data['phone'])
        if not re.fullmatch(r'\+56 [2-9] \d{4} \d{4}', valor):
            raise forms.ValidationError('Escribe un teléfono chileno: +56 9 1234 5678 o +56 2 2345 6789.')
        return valor

    def clean_whatsapp_number(self):
        digitos = normalizar_movil(self.cleaned_data['whatsapp_number'])
        if not digitos:
            raise forms.ValidationError('El WhatsApp debe ser un celular chileno: +56 9 XXXX XXXX.')
        return digitos

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        # Solo se procesa lo recién subido. False = "quitar foto"; un archivo ya
        # guardado = no la cambió.
        if isinstance(foto, UploadedFile):
            return procesar_foto(foto)
        return foto

    def save(self, commit=True):
        provider = super().save(commit=commit)
        if commit and self._foto_anterior and self._foto_anterior != (provider.foto.name or ''):
            provider.foto.storage.delete(self._foto_anterior)
        return provider

    def clean_website(self):
        valor = (self.cleaned_data.get('website') or '').strip()
        if valor and not re.match(r'https?://', valor, re.I):
            raise forms.ValidationError('Escribe la dirección completa, con https://')
        return valor

    def clean_instagram(self):
        """Acepta @usuario, usuario o el enlace completo; guarda solo el usuario."""
        valor = (self.cleaned_data.get('instagram') or '').strip()
        enlace = re.match(r'(?:https?://)?(?:www\.)?instagram\.com/([^/?#]+)', valor, re.I)
        if enlace:
            valor = enlace.group(1)
        valor = valor.lstrip('@').strip('/')
        if valor and not re.fullmatch(r'[A-Za-z0-9._]{1,30}', valor):
            raise forms.ValidationError('Escribe solo tu usuario de Instagram, por ejemplo: camila.kine')
        return valor

    def clean_fotos(self):
        nuevas = self.cleaned_data.get('fotos') or []
        quitar = set(self.data.getlist('quitar_fotos')) if hasattr(self.data, 'getlist') else set()
        actuales = self.instance.images.exclude(pk__in=[q for q in quitar if q.isdigit()]).count() \
            if self.instance.pk else 0
        if actuales + len(nuevas) > MAX_FOTOS:
            raise forms.ValidationError(
                f'Puedes tener hasta {MAX_FOTOS} fotos. Ya tienes {actuales}: quita alguna o sube menos.')
        return [procesar_foto(f, lado_maximo=1024) for f in nuevas]

    def guardar_fotos(self, provider):
        """Quita las marcadas, agrega las nuevas y deja una portada. Se llama
        después de guardar el perfil (al crear, el perfil no existía antes)."""
        quitar = [q for q in self.data.getlist('quitar_fotos') if q.isdigit()] if hasattr(self.data, 'getlist') else []
        for imagen in provider.images.filter(pk__in=quitar):
            imagen.image.storage.delete(imagen.image.name)
            imagen.delete()
        orden = (provider.images.order_by('-display_order').values_list('display_order', flat=True).first() or 0) + 1
        for n, archivo in enumerate(self.cleaned_data.get('fotos') or []):
            imagen = ProviderImage(provider=provider, display_order=orden + n,
                                   alt_text=f'Trabajo de {provider.business_name}'[:160])
            imagen.image.save(archivo.name, archivo, save=False)
            imagen.save()
        portada = self.data.get('portada') if hasattr(self.data, 'get') else None
        imagenes = provider.images.all()
        if portada and portada.isdigit() and imagenes.filter(pk=portada).exists():
            imagenes.update(is_cover=False)
            imagenes.filter(pk=portada).update(is_cover=True)
        elif imagenes.exists() and not imagenes.filter(is_cover=True).exists():
            primera = imagenes.order_by('display_order', 'pk').first()
            imagenes.filter(pk=primera.pk).update(is_cover=True)

    def clean_profession_title(self):
        return limpiar_texto(self.cleaned_data.get('profession_title', ''))

    def clean_institution(self):
        return limpiar_texto(self.cleaned_data.get('institution', ''))

    def clean_graduation_year(self):
        anio = self.cleaned_data.get('graduation_year')
        if anio is None:
            return None
        hoy = timezone.localdate().year
        if not 1950 <= anio <= hoy + 7:
            raise forms.ValidationError(f'Escribe un año entre 1950 y {hoy + 7}.')
        return anio

    def clean_health_registry(self):
        valor = ''.join(ch for ch in (self.cleaned_data.get('health_registry') or '') if not ch.isspace())
        if valor and not re.fullmatch(r'\d{3,10}', valor):
            raise forms.ValidationError('El registro de la Superintendencia de Salud es solo números.')
        return valor

    def clean(self):
        datos = super().clean()
        categoria = datos.get('category')
        anio = datos.get('graduation_year')
        # El registro de la Superintendencia es solo de salud: en otro rubro no
        # se guarda (no tendría cómo comprobarse y confunde en la ficha).
        if categoria and not categoria.pide_registro_salud:
            datos['health_registry'] = ''
        # Ofrecer atención de salud sin título es ejercicio ilegal de la
        # profesión. Quien está en práctica puede publicar igual, pero en lo
        # que ya puede hacer (clases, apoyo), no como kinesiólogo.
        if categoria and categoria.pide_registro_salud and anio and anio > timezone.localdate().year:
            self.add_error(
                'category',
                'La atención de salud solo puede ofrecerla quien ya está titulado/a. '
                'Mientras terminas, puedes publicar en otra categoría, como clases particulares.',
            )
        return datos

    def antispam_textos(self):
        return [self.data.get(k, '') for k in ('business_name', 'short_description', 'description', 'sector',
                                                 'service_area', 'profession_title', 'institution')]
