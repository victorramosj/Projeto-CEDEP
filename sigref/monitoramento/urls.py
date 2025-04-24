from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.conf import settings
from django.conf.urls.static import static
from . import views

# Router principal
router = DefaultRouter()
router.register(r'escolas', views.EscolaViewSet, basename='escolas')
router.register(r'setores', views.SetorViewSet, basename='setores')
router.register(r'usuarios', views.GREUserViewSet, basename='usuarios')
router.register(r'questionarios', views.QuestionarioViewSet, basename='questionarios')
router.register(r'monitoramentos', views.MonitoramentoViewSet, basename='monitoramentos')  # Adicionado
router.register(r'tipos-problema', views.TipoProblemaViewSet, basename='tipos-problema')
router.register(r'relatos-problema', views.RelatoProblemaViewSet, basename='relatos-problema')

# Rotas aninhadas para questionários
questionario_router = routers.NestedSimpleRouter(router, r'questionarios', lookup='questionario')
questionario_router.register(r'perguntas', views.PerguntaViewSet, basename='questionario-perguntas')

# Rotas aninhadas para monitoramentos (agora que monitoramentos está registrado)
monitoramento_router = routers.NestedSimpleRouter(router, r'monitoramentos', lookup='monitoramento')
monitoramento_router.register(r'respostas', views.RespostaViewSet, basename='monitoramento-respostas')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(questionario_router.urls)),
    path('', include(monitoramento_router.urls)),
    
    path('minhas-escolas/', views.MinhasEscolasView.as_view(), name='minhas-escolas'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)