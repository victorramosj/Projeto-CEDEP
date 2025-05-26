from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuartoViewSet, CamaViewSet, HospedeViewSet, ReservaViewSet, OcupacaoViewSet
from . import views

router = DefaultRouter()
router.register(r'quartos', QuartoViewSet, basename='quarto')
router.register(r'camas', CamaViewSet, basename='cama')
router.register(r'hospedes', HospedeViewSet, basename='hospede')
router.register(r'reservas', ReservaViewSet, basename='reserva')
router.register(r'ocupacoes', OcupacaoViewSet, basename='ocupacao')  # endpoint da ocupação

urlpatterns = [
    # Endpoints da API com prefixo /api/
    path('api/', include(router.urls)),
    
    
    # Páginas HTML para gerenciamento
    path('quartos/', views.gerenciar_quartos, name='gerenciar_quartos'),
    path('quartos/form/', views.quarto_form, name='quarto_form'),
    path('quartos/form/<int:pk>/', views.quarto_form, name='editar_quarto'),

    path('camas/', views.gerenciar_camas, name='gerenciar_camas'),
    path('camas/form/', views.cama_form, name='cama_form'),
    path('camas/form/<int:pk>/', views.cama_form, name='editar_cama'),
    path('camas_disponiveis/', views.camas_disponiveis, name='camas_disponiveis'),

    path('hospedes/', views.gerenciar_hospedes, name='gerenciar_hospedes'),
    path('hospedes/form/', views.hospede_form, name='hospede_form'),
    path('hospedes/form/<int:pk>/', views.hospede_form, name='editar_hospede'),
    path('hospedes/json/', views.listar_hospedes_json, name='listar_hospedes_json'),

    path('reservas/', views.gerenciar_reservas, name='gerenciar_reservas'),
    path('reservas/form/', views.reserva_form, name='reserva_form'),
    path('reservas/form/<int:pk>/', views.reserva_form, name='editar_reserva'),
    
    # Páginas HTML para gerenciamento de Ocupações
    path('ocupacoes/', views.gerenciar_ocupacoes, name='gerenciar_ocupacoes'),
    path('ocupacoes/form/', views.ocupacao_form, name='ocupacao_form'),
    path('ocupacoes/form/<int:pk>/', views.ocupacao_form, name='editar_ocupacao'),

    path('relatorio/reservas/', views.reservas_report_pdf, name='reservas_report_pdf'),
    path('relatorio/ocupacoes/', views.ocupacoes_report_pdf, name='ocupacoes_report_pdf'),

    path('dashboard_hospedagens/', views.dashboard, name='dashboard_hospedagens'),
    path('mapa-interativo/', views.mapa_interativo, name='mapa_interativo'),
]
