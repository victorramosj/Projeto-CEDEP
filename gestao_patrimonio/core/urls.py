from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BemViewSet,
    MovimentacaoViewSet,
    dashboard,
    criar_bem,
    criar_categoria,
    criar_departamento,
    criar_fornecedor,
    bem_form_view,
    gerenciar_bens,
    editar_bem,
    simular_rfid,
    excluir_bem,
    editar_bem_api,
    buscar_tags_rfid,
    historico_item,   
)

router = DefaultRouter()
router.register(r'bens', BemViewSet)
router.register(r'movimentacoes', MovimentacaoViewSet)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('bens/form/', bem_form_view, name='bem_form'), 
    path('bens/gerenciar/', gerenciar_bens, name='gerenciar_bens'),  # nova rota
    path('bens/editar/<int:pk>/', editar_bem, name='editar_bem'),

    # Rotas de criação rápida
    path('api/', include(router.urls)), 
    path('bens/novo/', criar_bem, name='criar_bem'),
    path('bens/excluir/<int:pk>/', excluir_bem, name='excluir_bem'),
    path('bens/editar_api/<int:pk>/', editar_bem_api, name='editar_bem_api'),
    path('criar_categoria/', criar_categoria, name='criar_categoria'),
    path('criar_departamento/', criar_departamento, name='criar_departamento'),
    path('criar_fornecedor/', criar_fornecedor, name='criar_fornecedor'),
    

    #simular rfid
    path('simular_rfid/', simular_rfid, name='simular_rfid'),
    path('buscar-tags-rfid/', buscar_tags_rfid, name='buscar_tags_rfid'),
    
    #historico
    path('historico_item/<int:bem_id>/', historico_item, name='historico_item'),
]
