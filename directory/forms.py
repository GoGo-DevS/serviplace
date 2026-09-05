from django import forms
from django.utils.html import strip_tags

from core.antispam import AntispamFormMixin

from .models import ProviderReport


def _plano(valor):
    return ' '.join(strip_tags(valor or '').split()).strip()


class ProviderReportForm(AntispamFormMixin, forms.ModelForm):
    """Reportar / pedir baja / corregir / reclamar un perfil. Lo llena cualquiera."""

    class Meta:
        model = ProviderReport
        fields = ['kind', 'reporter_name', 'reporter_contact', 'message']
        labels = {
            'kind': '¿Qué quieres hacer?',
            'reporter_name': 'Tu nombre',
            'reporter_contact': 'Cómo te contactamos (WhatsApp o correo)',
            'message': 'Cuéntanos',
        }
        widgets = {
            'kind': forms.RadioSelect(),
            'message': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reporter_name'].required = True
        self.fields['reporter_contact'].required = True
        for name, field in self.fields.items():
            if name.startswith('sitio_web') or name.startswith('sello_') or name == 'kind':
                continue
            field.widget.attrs['class'] = 'form-control'

    def clean_reporter_name(self):
        return _plano(self.cleaned_data['reporter_name'])

    def clean_reporter_contact(self):
        return _plano(self.cleaned_data['reporter_contact'])

    def clean_message(self):
        texto = strip_tags(self.cleaned_data['message']).strip()
        if len(texto) < 10:
            raise forms.ValidationError('Cuéntanos un poco más (mínimo 10 caracteres).')
        return texto

    def antispam_textos(self):
        return [self.data.get('message', ''), self.data.get('reporter_name', ''), self.data.get('reporter_contact', '')]
