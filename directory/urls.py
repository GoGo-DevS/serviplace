from django.urls import path

from . import views

app_name = 'directory'

urlpatterns = [
    path('servicios/', views.provider_list, name='provider_list'),
    path('prestadores/<slug:slug>/', views.provider_detail, name='provider_detail'),
    path('prestadores/<slug:slug>/whatsapp/', views.whatsapp_redirect, name='whatsapp_redirect'),
]
