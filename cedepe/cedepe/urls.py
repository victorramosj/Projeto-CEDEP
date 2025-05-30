from django.contrib import admin
from cedepe import views # Importe as views do app principal
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('reservas/', include('reservas.urls')),  # Inclui as URLs do app reservas
    path('eventos/', include('eventos.urls')),  # Inclui as URLs do app reservas
    path('monitoramento/', include('monitoramento.urls')), 
    path('', views.dashboard, name='home'),  # View principal
    # Rotas de autenticação
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),

    # Rotas de recuperação de senha
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='cedepe/password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='cedepe/password_reset_done.html'), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='cedepe/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='cedepe/password_reset_complete.html'), name='password_reset_complete'),
]
