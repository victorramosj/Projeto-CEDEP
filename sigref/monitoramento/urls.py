from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.conf import settings
from django.conf.urls.static import static
from . import views

# -----------------------------
# DRF: Registro de ViewSets
# -----------------------------
router = DefaultRouter()
router.register(r'escolas', views.EscolaViewSet, basename='escolas')
router.register(r'setores', views.SetorViewSet, basename='setores')
router.register(r'usuarios', views.GREUserViewSet, basename='usuarios')
router.register(r'questionarios', views.QuestionarioViewSet, basename='questionarios')
router.register(r'monitoramentos', views.MonitoramentoViewSet, basename='monitoramentos')
router.register(r'tipos-problema', views.TipoProblemaViewSet, basename='tipos-problema')
router.register(r'relatos-problema', views.RelatoProblemaViewSet, basename='relatos-problema')

# Rotas aninhadas para Questionários e Perguntas
questionario_router = routers.NestedSimpleRouter(router, r'questionarios', lookup='questionario')
questionario_router.register(r'perguntas', views.PerguntaViewSet, basename='questionario-perguntas')

# Rotas aninhadas para Monitoramentos e Respostas
monitoramento_router = routers.NestedSimpleRouter(router, r'monitoramentos', lookup='monitoramento')
monitoramento_router.register(r'respostas', views.RespostaViewSet, basename='monitoramento-respostas')

urlpatterns = [
    # -----------------------------
    # Views de template (front-end)
    # -----------------------------
    path('minhas-escolas/', views.MinhasEscolasView.as_view(), name='minhas-escolas'),

    # Monitoramentos gerais
    path('dashboard/monitoramentos/', views.dashboard_monitoramentos, name='dashboard_monitoramentos'),
    path('relatos/problemas/', views.RelatosProblemasView.as_view(), name='relatos_problemas'),
    path('monitoramentos/<int:pk>/', views.DetalheMonitoramentoView.as_view(), name='detalhe_monitoramento'),
    path('fluxo/', views.fluxo_monitoramento, name='fluxo_monitoramento_setores'),

    # Fluxo de Questionários
    path('questionarios/novo/<int:setor_id>/', 
        views.criar_questionario_view, 
        name='criar-questionario'),
    path('questionarios/gerenciar/', views.GerenciarQuestionariosView.as_view(), name='gerenciar_questionarios'),
    path('questionarios/<int:pk>/', views.DetalheMonitoramentoView.as_view(), name='detalhe_questionario'),    
    path('questionarios/<int:pk>/perguntas/frontend/', 
     views.GerenciarPerguntasView.as_view(), 
     name='gerenciar_perguntas'),
    #respostas Monitoramentos
    path('escolas/', views.SelecionarEscolaView.as_view(), name='selecionar_escola'),
    path('escola/<int:escola_id>/questionarios/', views.QuestionariosEscolaView.as_view(), name='questionarios_escola'),
    path(
        'escola/<int:escola_id>/questionario/<int:questionario_id>/responder/',
        views.ResponderQuestionarioView.as_view(),
        name='responder_questionario'
    ),
    # Dashboard e relatórios da Escola
    path('escola/dashboard/', views.EscolaDashboardView.as_view(), name='escola_dashboard'),
    path('escola/relatar-problema/', views.RelatoProblemaCreateView.as_view(), name='relatar_problema'),
    

    # -----------------------------
    # Endpoints AJAX / API customizados
    # -----------------------------
    path('api/questionarios/create/', views.QuestionarioCreateAPI.as_view(), name='questionarios-add'),
    path('api/questionarios/<int:pk>/assign_escolas/', views.AssignEscolasQuestionario.as_view(), name='assign_escolas'),
    path('api/questionarios/<int:pk>/escolas/', views.QuestionarioEscolasView.as_view(), name='questionario-escolas'),


    # -----------------------------
    # DRF: Inclusão automática de rotas
    # -----------------------------
   
    path('', include(router.urls)),
    path('', include(questionario_router.urls)),    
    path('', include(monitoramento_router.urls)),
]

# Servir arquivos de mídia em DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
