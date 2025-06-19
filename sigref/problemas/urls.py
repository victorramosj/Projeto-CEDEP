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
    deletar_lacunas_api,
    deletar_problemas_api,
    confirmar_visualizacao_aviso,
    lista_problemas_por_escola,
    lista_lacunas_por_escola,
)

# Criando o roteador para as views baseadas em viewsets
router = routers.DefaultRouter()
router.register(r'lacunas', LacunaViewSet, basename='lacunas')
router.register(r'problemas-usuario', ProblemaUsuarioViewSet, basename='problemas-usuario')
router.register(r'avisos', AvisoImportanteViewSet, basename='avisos')

urlpatterns = [
    # Visualização da dashboard
    path('escola/dashboard/', EscolaDashboardView.as_view(), name='escola_dashboard'),
    path('escola/dashboard/<int:escola_id>/', EscolaDashboardView.as_view(), name='dashboard_escola'),

    # PROBLEMAS/LACUNA
    path('dashboard/', views.problema_dashboard_view, name='problemas'),
    path('relatar-problema/<int:escola_id>/', views.relatar_problema_view, name='relatar_problema'),
    path('relatar-lacuna/<int:escola_id>/', views.relatar_lacuna_view, name='relatar_lacuna'),   

    path('alertas/', views.dashboard, name='alertas'),
    
    # --- ALTERAÇÃO AQUI ---
    # Rota para a lista GERAL de lacunas (TODAS as escolas)
    path('lacunas/', views.tela_lacuna_view, name='tela_lacunas'),
    # Rota para a lista GERAL de problemas (TODOS os problemas)
    path('problemas/', views.tela_problema_view, name='tela_problemas'),

    # APIs ---------------------------------------------------------------------------------
    path('api/lacuna/atualizar-status/<int:lacuna_id>/', UpdateStatusLacuna.as_view(), name='api_atualizar_status_lacuna'),
    path('api/lacunas/deletar/', views.deletar_lacunas_api, name='api_deletar_lacunas'),
    path('api/problema/atualizar-status/<int:problema_id>/', UpdateStatusProblema.as_view(), name='api_atualizar_status_problema'),
    path('api/problemas/deletar/', views.deletar_problemas_api, name='api_deletar_problemas'),

    # AVISOS---------------------------------------------------------------------------------
    path('avisos/criar/', criar_aviso_view, name='criar_aviso'),
    path('avisos/', views.listar_avisos_view, name='listar_avisos'),
    path('avisos/editar/<int:aviso_id>/', views.editar_aviso_view, name='editar_aviso'),
    path('avisos/apagar/<int:aviso_id>/', views.apagar_aviso_view, name='apagar_aviso'),
    path('apagar_varios_avisos/', views.apagar_varios_avisos, name='apagar_varios_avisos'),

    # NOVAS URLS
    path('problemas/avisos/verificar-automaticos/', views.verificar_avisos_automaticos, name='verificar_avisos_automaticos'),
    path('problemas/avisos/apagar-automaticos/', views.apagar_avisos_automaticos, name='apagar_avisos_automaticos'),

    path('confirmar-visualizacao/<int:aviso_id>/', confirmar_visualizacao_aviso, name='confirmar_visualizacao_aviso'),

    # Rota para listar problemas de UMA escola específica
    path('escola/<int:escola_id>/problemas/', views.lista_problemas_por_escola, name='lista_problemas_escola'),
    # Rota para listar lacunas de UMA escola específica
    path('escola/<int:escola_id>/lacunas/', views.lista_lacunas_por_escola, name='lista_lacunas_escola'),
]

urlpatterns += router.urls