from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import (
    RelatorioDiarioView, 
    QuestionariosEscolaAPIView, 
    EscolaSelectionAPIView, 
    EscolaDashboardAPIView, 
    ConfirmarVisualizacaoAvisoAPIView,
    ResponderQuestionarioAPIView,
    AllOfflineDataAPIView
)

# -----------------------------------------
# DRF: Registro de ViewSets principais
# -----------------------------------------
router = DefaultRouter()
router.register(r'escolas', views.EscolaViewSet, basename='escolas')
router.register(r'setores', views.SetorViewSet, basename='setores')
router.register(r'usuarios', views.GREUserViewSet, basename='usuarios')
router.register(r'questionarios', views.QuestionarioViewSet, basename='questionarios')
router.register(r'monitoramentos', views.MonitoramentoViewSet, basename='monitoramentos')

# -----------------------------------------
# DRF: Rotas aninhadas (Nested Routers)
# -----------------------------------------
questionario_router = routers.NestedSimpleRouter(router, r'questionarios', lookup='questionario')
questionario_router.register(r'perguntas', views.PerguntaViewSet, basename='questionario-perguntas')

monitoramento_router = routers.NestedSimpleRouter(router, r'monitoramentos', lookup='monitoramento')
monitoramento_router.register(r'respostas', views.RespostaViewSet, basename='monitoramento-respostas')

# -----------------------------------------
# URL Patterns
# -----------------------------------------
urlpatterns = [
    # -----------------------------------------
    # Views baseadas em templates (front-end)
    # -----------------------------------------
    path('dashboard/', views.dashboard_monitoramentos, name='dashboard_monitoramentos'),
    
    #relatórios
    path('escola/<int:escola_id>/relatorio-diario/', RelatorioDiarioView.as_view(), 
         name='relatorio_diario'),
    path('detalhes/<int:pk>/', views.DetalheMonitoramentoView.as_view(), name='detalhe_monitoramento'),
    path('relatorio-monitoramentos/', views.RelatorioMonitoramentosView.as_view(), name='relatorio_monitoramentos'),
    
    # passo a passo para criação de questionários
    path('fluxo/', views.fluxo_monitoramento, name='fluxo_monitoramento_setores'),
    
    # Questionários
    path('questionarios/novo/<int:setor_id>/', views.criar_questionario_view, name='criar-questionario'),
    path('questionarios/gerenciar/', views.GerenciarQuestionariosView.as_view(), name='gerenciar_questionarios'),
    path('questionarios/<int:pk>/', views.DetalheMonitoramentoView.as_view(), name='detalhe_questionario'),
    path('questionarios/<int:pk>/perguntas/frontend/', views.GerenciarPerguntasView.as_view(), name='gerenciar_perguntas'),
    path('questionario/<int:questionario_id>/graficos/', views.visualizar_graficos_questionario, name='visualizar_graficos_questionario'), 
    
    # Escolas e respostas (views HTML)
    path('selecionar_escola/', views.SelecionarEscolaView.as_view(), name='selecionar_escola'),
    path('escola/<int:escola_id>/questionarios/', views.QuestionariosEscolaView.as_view(), name='questionarios_escola'),
    path('escola/<int:escola_id>/questionario/<int:questionario_id>/responder/', views.ResponderQuestionarioView.as_view(), name='responder_questionario'), 
    
    # -----------------------------------------
    # Endpoints AJAX / API customizadas
    # -----------------------------------------
    path('api/questionarios/create/', views.QuestionarioCreateAPI.as_view(), name='questionarios-add'),
    path('api/questionarios/<int:pk>/assign_escolas/', views.AssignEscolasQuestionario.as_view(), name='assign_escolas'),
    path('api/questionarios/<int:pk>/escolas/', views.QuestionarioEscolasView.as_view(), name='questionario-escolas'),
    path('api/greuser-search/', views.greuser_search, name='greuser_search'),
    path('api/escolas-selection/', EscolaSelectionAPIView.as_view(), name='escola-selection-api'),
    
    # Rotas para o Dashboard da Escola
    path('api/escola-dashboard/', EscolaDashboardAPIView.as_view(), name='escola-dashboard-api-no-id'),
    path('api/escola-dashboard/<int:escola_id>/', EscolaDashboardAPIView.as_view(), name='escola-dashboard-api'),
    path('api/avisos/<int:aviso_id>/confirmar-visualizacao/', ConfirmarVisualizacaoAvisoAPIView.as_view(), name='confirmar-visualizacao-aviso-api'),

    # ROTA PARA RESPONDER QUESTIONÁRIO (API)
    path('api/escola/<int:escola_id>/questionario/<int:questionario_id>/responder/', ResponderQuestionarioAPIView.as_view(), name='api-responder-questionario'),

    # ROTA PARA LISTAR QUESTIONÁRIOS POR ESCOLA (API)
    path('api/escola/<int:escola_id>/questionarios/', QuestionariosEscolaAPIView.as_view(), name='api-questionarios-escola'),
    path('api/all-offline-data/', AllOfflineDataAPIView.as_view(), name='all-offline-data-api'), # <--- NOVA ROTA
    # -----------------------------------------
    # DRF: Inclusão de ViewSets e Nested Routers
    # -----------------------------------------
    path('', include(router.urls)),
    path('', include(questionario_router.urls)),
    path('', include(monitoramento_router.urls)),
    path('', include('problemas.urls')),
]

# -----------------------------------------
# Arquivos de mídia em ambiente DEBUG
# -----------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
