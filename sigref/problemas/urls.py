from rest_framework import routers
from .views import LacunaViewSet, ProblemaUsuarioViewSet

router = routers.DefaultRouter()
router.register(r'lacunas', LacunaViewSet, basename='lacunas')
router.register(r'problemas-usuario', ProblemaUsuarioViewSet, basename='problemas-usuario')

urlpatterns = router.urls


from django.urls import path
from . import views
from .views import criar_aviso_view

urlpatterns = [
    path('escola/dashboard/', views.EscolaDashboardView.as_view(), name='escola_dashboard'),
    path('dashboard/', views.problema_dashboard_view, name='problemas'),
    path('relatar-problema/', views.relatar_problema_view, name='relatar_problema'),
    path('avisos/criar/', criar_aviso_view, name='criar_aviso'),
    path('avisos/', views.listar_avisos_view, name='listar_avisos'),
    path('avisos/criar/', views.criar_aviso_view, name='criar_aviso'),
]


