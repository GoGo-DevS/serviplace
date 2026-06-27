from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('sumate/', views.join, name='join'),
    path('sobre-serviplace/', views.about, name='about'),
    path('contacto/', views.contact, name='contact'),
    path('seguridad-y-confianza/', views.trust_and_safety, name='trust_and_safety'),
]
