from django import forms

from .models import ProviderApplication


class ProviderApplicationForm(forms.ModelForm):
    class Meta:
        model = ProviderApplication
        fields = [
            'nombre_negocio',
            'nombre_contacto',
            'categoria',
            'telefono',
            'whatsapp',
            'instagram',
            'website',
            'anos_experiencia',
            'horario_atencion',
            'sector',
            'descripcion_servicio',
            'acepta_contacto',
        ]
        labels = {
            'nombre_negocio': 'Nombre del negocio o servicio',
            'nombre_contacto': 'Nombre de contacto',
            'categoria': 'Categoría principal',
            'telefono': 'Teléfono',
            'whatsapp': 'WhatsApp',
            'instagram': 'Instagram',
            'website': 'Sitio web',
            'anos_experiencia': 'Años de experiencia',
            'horario_atencion': 'Horario de atención',
            'sector': 'Sector o zona donde atiendes',
            'descripcion_servicio': 'Describe tu servicio',
            'acepta_contacto': 'Acepto que SERVIPLACE me contacte para revisar mi información.',
        }
        widgets = {
            'nombre_negocio': forms.TextInput(attrs={'placeholder': 'Ej: Gasfiter Express'}),
            'nombre_contacto': forms.TextInput(attrs={'placeholder': 'Tu nombre'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+56 9 1234 5678'}),
            'whatsapp': forms.TextInput(attrs={'placeholder': '+56 9 1234 5678'}),
            'instagram': forms.TextInput(attrs={'placeholder': 'Ej: @miservicio'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://tusitio.cl'}),
            'anos_experiencia': forms.NumberInput(attrs={'min': 0, 'placeholder': 'Ej: 5'}),
            'horario_atencion': forms.TextInput(attrs={'placeholder': 'Ej: Lunes a sábado, 9:00 a 19:00'}),
            'sector': forms.TextInput(attrs={'placeholder': 'Ej: Centro, Rinconada, zona norte'}),
            'descripcion_servicio': forms.Textarea(
                attrs={
                    'rows': 5,
                    'placeholder': 'Cuenta que haces, en qué sectores atiendes y qué tipo de trabajos recibes.',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'acepta_contacto':
                field.widget.attrs.update({'class': 'form-check-input'})
                field.required = True
            else:
                field.widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['categoria'].widget.attrs.update({'class': 'form-select form-select-lg'})
        self.fields['categoria'].queryset = self.fields['categoria'].queryset.filter(is_active=True)
