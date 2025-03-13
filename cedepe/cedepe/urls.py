
from django.contrib import admin
from django.urls import path
from gestao_patrimonio import views  # Importe as views do app principal
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
     # Rotas de autenticação
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),

    # Rotas de recuperação de senha
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='gestao_patrimonio/password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='gestao_patrimonio/password_reset_done.html'), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='gestao_patrimonio/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='gestao_patrimonio/password_reset_complete.html'), name='password_reset_complete'),

]
