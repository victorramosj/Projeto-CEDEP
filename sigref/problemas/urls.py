from rest_framework import routers
from django.urls import path
from . import views 
from .views import (
    LacunaViewSet,
    ProblemaUsuarioViewSet,
    EscolaDashboardView,
    relatar_lacuna_view,
    criar_aviso_view,
    listar_avisos_view,
    relatar_problema_view,
    problema_dashboard_view,
)


router = routers.DefaultRouter()
router.register(r'lacunas', LacunaViewSet, basename='lacunas')
router.register(r'problemas-usuario', ProblemaUsuarioViewSet, basename='problemas-usuario')

urlpatterns = [
    path('escola/dashboard/', EscolaDashboardView.as_view(), name='escola_dashboard'),
    path('dashboard/', problema_dashboard_view, name='problemas'),
    path('relatar-lacuna/', relatar_lacuna_view, name='relatar_lacuna'),
    path('relatar-problema/', relatar_problema_view, name='relatar_problema'),
    path('avisos/', listar_avisos_view, name='listar_avisos'),
    path('avisos/criar/', criar_aviso_view, name='criar_aviso'),
    path('avisos/editar/<int:aviso_id>/', views.editar_aviso_view, name='editar_aviso'),
    path('avisos/apagar/<int:aviso_id>/', views.apagar_aviso_view, name='apagar_aviso'),
    path('escolas/', views.listar_escolas, name='listar_escolas'),

    

]

urlpatterns += router.urls
