from django.urls import path

from . import metricas, views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('sumate/', views.join, name='join'),
    path('profesionales/', views.para_profesionales, name='para_profesionales'),
    path('cuenta/metricas/', metricas.metricas, name='metricas'),
    path('sobre-serviplace/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('seguridad-y-confianza/', views.trust_and_safety, name='trust_and_safety'),
    path('terminos-de-uso/', views.terms, name='terms'),
]
