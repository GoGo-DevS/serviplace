from django import template

register = template.Library()


@register.filter
def otros_rubros(provider, mostrado):
    """Nombres de los rubros del perfil, menos el que ya muestra la tarjeta."""
    pk = getattr(mostrado, 'pk', None)
    return [c.name for c in provider.rubros if c.pk != pk]
