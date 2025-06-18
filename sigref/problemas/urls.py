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
    confirmar_visualizacao_aviso,  # Importação da função
)

# Criando o roteador para as views baseadas em viewsets
router = routers.DefaultRouter()
router.register(r'lacunas', LacunaViewSet, basename='lacunas')
router.register(r'problemas-usuario', ProblemaUsuarioViewSet, basename='problemas-usuario')
router.register(r'avisos', AvisoImportanteViewSet, basename='avisos')

urlpatterns = [
    # Visualização da dashboard
    path('escola/dashboard/', EscolaDashboardView.as_view(), name='escola_dashboard'),
    
    # URL para acessar uma escola específica, para monitores e administradores
    path('escola/dashboard/<int:escola_id>/', EscolaDashboardView.as_view(), name='dashboard_escola'),

    # PROBLEMAS/LACUNA
    path('dashboard/', views.problema_dashboard_view, name='problemas'),
    path('relatar-problema/<int:escola_id>/', views.relatar_problema_view, name='relatar_problema'),
    path('relatar-lacuna/<int:escola_id>/', views.relatar_lacuna_view, name='relatar_lacuna'),  
    path('problemas/lacunas/', views.tela_lacuna_view, name='tela_lacunas'),
    path('problema/problemas/', views.tela_problema_view, name='tela_problemas'),

    path('alertas/', views.dashboard, name='alertas'),
    path('tela_lacunas/', views.tela_lacuna_view, name='tela_lacunas'),
    path('tela_problemas/', views.tela_problema_view, name='tela_problemas'),

    # API Tela Lacuna
    path('api/lacuna/atualizar-status/<int:lacuna_id>/', UpdateStatusLacuna.as_view(), name='api_atualizar_status_lacuna'),
    # API Tela Problema
    path('api/problema/atualizar-status/<int:problema_id>/', UpdateStatusProblema.as_view(), name='api_atualizar_status_problema'),
        
    # AVISOS
    path('avisos/criar/', criar_aviso_view, name='criar_aviso'),
    # URL para listar avisos (apenas uma vez)
    path('avisos/', views.listar_avisos_view, name='listar_avisos'),
    # URL para editar aviso
    path('avisos/editar/<int:aviso_id>/', views.editar_aviso_view, name='editar_aviso'),
    # URL para apagar aviso
    path('avisos/apagar/<int:aviso_id>/', views.apagar_aviso_view, name='apagar_aviso'),
    # URL para apagar vários avisos
    path('apagar_varios_avisos/', views.apagar_varios_avisos, name='apagar_varios_avisos'),

    # NOVAS URLS
    path('problemas/avisos/verificar-automaticos/', views.verificar_avisos_automaticos, name='verificar_avisos_automaticos'),
    path('problemas/avisos/apagar-automaticos/', views.apagar_avisos_automaticos, name='apagar_avisos_automaticos'),
    
    path('tela_lacunas/', views.tela_lacuna_view, name='tela_lacuna_view'),

    # Confirmação de visualização do aviso
    path('confirmar-visualizacao/<int:aviso_id>/', confirmar_visualizacao_aviso, name='confirmar_visualizacao_aviso'),
]

urlpatterns += router.urls
