from rest_framework import routers
from .views import LacunaViewSet, ProblemaUsuarioViewSet, EscolaDashboardView, relatar_lacuna_view

router = routers.DefaultRouter()
router.register(r'lacunas', LacunaViewSet, basename='lacunas')
router.register(r'problemas-usuario', ProblemaUsuarioViewSet, basename='problemas-usuario')

urlpatterns = router.urls


from django.urls import path
from . import views

urlpatterns = [
    path('escola/dashboard/', views.EscolaDashboardView.as_view(), name='escola_dashboard'),
    path('dashboard/', views.problema_dashboard_view, name='problemas'),
    path('relatar-lacuna/', relatar_lacuna_view, name='relatar_lacuna'),
    path('relatar-problema/', views.relatar_problema_view, name='relatar_problema')
]

