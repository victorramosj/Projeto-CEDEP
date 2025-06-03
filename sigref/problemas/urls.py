from rest_framework import routers
from .views import LacunaViewSet, ProblemaUsuarioViewSet, EscolaDashboardView, relatar_lacuna_view

router = routers.DefaultRouter()
router.register(r'lacunas', LacunaViewSet, basename='lacunas')
router.register(r'problemas-usuario', ProblemaUsuarioViewSet, basename='problemas-usuario')

urlpatterns = router.urls


from django.urls import path
from . import views
from .views import criar_aviso_view

urlpatterns = [
    #Visualização da dashboard
    # URL para a escola associada ao usuário (sem precisar passar o escola_id para 'escola' tipo)
    path('escola/dashboard/', EscolaDashboardView.as_view(), name='escola_dashboard'),
    
    # URL para acessar uma escola específica, para monitores e administradores
    path('escola/<int:escola_id>/', EscolaDashboardView.as_view(), name='dashboard_escola'),

    #PROBLEMAS/LACUNA
    path('dashboard/', views.problema_dashboard_view, name='problemas'),
    path('relatar-problema/', views.relatar_problema_view, name='relatar_problema'),
    path('relatar-lacuna/', relatar_lacuna_view, name='relatar_lacuna'),
        
    #AVISOS
    path('avisos/criar/', criar_aviso_view, name='criar_aviso'),
    path('avisos/', views.listar_avisos_view, name='listar_avisos'),
    path('avisos/criar/', views.criar_aviso_view, name='criar_aviso'),
]


