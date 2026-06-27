from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('cuenta/registro/', views.register, name='register'),
    path('cuenta/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('cuenta/logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
    path('cuenta/dashboard/', views.dashboard, name='dashboard'),
    path('cuenta/publicar/', views.provider_create, name='provider_create'),
    path('cuenta/mi-perfil/<slug:slug>/editar/', views.provider_edit, name='provider_edit'),
    path('prestadores/<slug:slug>/reclamar/', views.claim_profile, name='claim_profile'),
    path('hazte-verificado/', views.hazte_verificado, name='hazte_verificado'),
]
