import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.html import strip_tags

from core.antispam import AntispamFormMixin
from directory.models import Category, Commune, Provider

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


class RegisterForm(AntispamFormMixin, UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    whatsapp = forms.CharField(
        max_length=30,
        required=False,
        label='WhatsApp (opcional)',
        help_text='Ej: +56 9 1234 5678',
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

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo. ¿Quieres iniciar sesión?')
        return email

    def antispam_textos(self):
        return [self.data.get('username', ''), self.data.get('email', '')]


class ProviderForm(AntispamFormMixin, forms.ModelForm):
    class Meta:
        model = Provider
        fields = [
            'business_name',
            'contact_name',
            'category',
            'commune',
            'sector',
            'short_description',
            'description',
            'phone',
            'whatsapp_number',
            'email',
            'address',
            'service_area',
        ]
        labels = {
            'business_name': 'Nombre del negocio o cómo te conocen',
            'contact_name': 'Tu nombre',
            'category': 'Rubro',
            'commune': 'Comuna base',
            'sector': 'Sector o barrio',
            'short_description': 'En una frase, qué haces',
            'description': 'Cuéntale al vecino qué haces y cómo trabajas',
            'phone': 'Teléfono',
            'whatsapp_number': 'WhatsApp',
            'email': 'Correo (opcional)',
            'address': 'Dirección (opcional)',
            'service_area': 'Dónde atiendes (opcional)',
        }
        help_texts = {
            'short_description': 'Máximo 220 caracteres. Es lo que se ve en la tarjeta.',
            'whatsapp_number': 'Celular chileno. Es el botón principal de tu perfil.',
            'service_area': 'Ej: Maipú, Cerrillos y Pudahuel',
        }
        widgets = {
            'short_description': forms.TextInput(attrs={'maxlength': 220, 'placeholder': 'Ej: Gásfiter con 10 años de experiencia, urgencias 24/7'}),
            'description': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Qué trabajos haces, en qué sectores, horarios, si entregas boleta o garantía…'}),
            'sector': forms.TextInput(attrs={'placeholder': 'Ej: Ciudad Satélite'}),
            'phone': forms.TextInput(attrs={'placeholder': '+56 9 1234 5678', 'inputmode': 'tel'}),
            'whatsapp_number': forms.TextInput(attrs={'placeholder': '+56 9 1234 5678', 'inputmode': 'tel'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['commune'].queryset = Commune.objects.filter(is_active=True).select_related('region').order_by('name')
        self.fields['category'].empty_label = 'Elige un rubro'
        self.fields['commune'].empty_label = 'Elige tu comuna'
        for name, field in self.fields.items():
            if name.startswith('sitio_web') or name.startswith('sello_'):
                continue
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
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

    def antispam_textos(self):
        return [self.data.get(k, '') for k in ('business_name', 'short_description', 'description', 'sector', 'service_area')]
