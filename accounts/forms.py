from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from directory.models import Category, Commune, Provider

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    whatsapp = forms.CharField(
        max_length=30,
        required=False,
        label='WhatsApp (opcional)',
        help_text='Ej: +56912345678',
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['username'].help_text = 'Solo letras, números y @/./+/-/_'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ProviderForm(forms.ModelForm):
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
            'business_name': 'Nombre del negocio',
            'contact_name': 'Nombre de contacto',
            'category': 'Categoría',
            'commune': 'Comuna',
            'sector': 'Sector / Barrio',
            'short_description': 'Descripción corta (máx. 220 caracteres)',
            'description': 'Descripción completa del servicio',
            'phone': 'Teléfono',
            'whatsapp_number': 'Número WhatsApp',
            'email': 'Email (opcional)',
            'address': 'Dirección (opcional)',
            'service_area': 'Área de atención (opcional)',
        }
        widgets = {
            'short_description': forms.TextInput(),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['commune'].queryset = Commune.objects.filter(is_active=True).order_by('name')
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = f'{css} form-select'.strip()
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = f'{css} form-control'.strip()
            else:
                field.widget.attrs['class'] = f'{css} form-control'.strip()
