from django.urls import path
from . import views
from rest_framework import routers
from .views import (
    LacunaViewSet,
    ProblemaUsuarioViewSet,
    EscolaDashboardView,
    AvisoImportanteViewSet,
    relatar_lacuna_view,
    criar_aviso_view,
    listar_avisos_view,
    relatar_problema_view,
    problema_dashboard_view,
    UpdateStatusLacuna,
    UpdateStatusProblema,
    tela_lacuna_view,
    tela_problema_view,

)

# Criando o roteador para as views baseadas em viewsets
router = routers.DefaultRouter()
router.register(r'lacunas', LacunaViewSet, basename='lacunas')
router.register(r'problemas-usuario', ProblemaUsuarioViewSet, basename='problemas-usuario')
router.register(r'avisos', AvisoImportanteViewSet, basename='avisos')  # Novo

urlpatterns = [
    #Visualização da dashboard
    # URL para a escola associada ao usuário (sem precisar passar o escola_id para 'escola' tipo)
    path('escola/dashboard/', EscolaDashboardView.as_view(), name='escola_dashboard'),
    
    # URL para acessar uma escola específica, para monitores e administradores
    path('escola/dashboard/<int:escola_id>/', EscolaDashboardView.as_view(), name='dashboard_escola'),

    #PROBLEMAS/LACUNA
    path('dashboard/', views.problema_dashboard_view, name='problemas'),
    path('relatar-problema/<int:escola_id>/', views.relatar_problema_view, name='relatar_problema'),
    path('relatar-lacuna/<int:escola_id>/', views.relatar_lacuna_view, name='relatar_lacuna'),  
    path('problemas/lacunas/', views.tela_lacuna_view, name='tela_lacunas'),
    path('problema/problemas/', views.tela_problema_view, name='tela_problemas'),

    #API Tela Lacuna
    path('lacuna/<int:lacuna_id>/alterar_status/', UpdateStatusLacuna.as_view(), name='alterar_status_lacuna'),

    #API Tela Problema
   
    #AVISOS
    path('avisos/criar/', criar_aviso_view, name='criar_aviso'),
    path('avisos/', views.listar_avisos_view, name='listar_avisos'),
    path('avisos/criar/', views.criar_aviso_view, name='criar_aviso'),

    # URL para editar aviso
    path('avisos/editar/<int:aviso_id>/', views.editar_aviso_view, name='editar_aviso'),
    

    # URL para apagar aviso
    path('avisos/apagar/<int:aviso_id>/', views.apagar_aviso_view, name='apagar_aviso'),

    # URL para listar avisos
    path('avisos/', views.listar_avisos_view, name='listar_avisos'),


]

urlpatterns += router.urls
