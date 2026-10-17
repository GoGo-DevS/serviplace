from django.urls import path

from . import views

app_name = 'directory'

# URLs limpias por especialidad y comuna (18-10-2026). `en/<comuna>/` va antes
# que `<rubro>/<comuna>/`: si no, "en" se leería como una especialidad.
urlpatterns = [
    path('servicios/', views.provider_list, name='provider_list'),
    path('servicios/en/<slug:comuna>/', views.listado_comuna, name='listado_comuna'),
    path('servicios/<slug:rubro>/', views.listado_rubro, name='listado_rubro'),
    path('servicios/<slug:rubro>/<slug:comuna>/', views.listado_rubro_comuna, name='listado_rubro_comuna'),
    path('prestadores/<slug:slug>/', views.provider_detail, name='provider_detail'),
    path('prestadores/<slug:slug>/whatsapp/', views.whatsapp_redirect, name='whatsapp_redirect'),
]
