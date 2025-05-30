from rest_framework import routers
from .views import LacunaViewSet, ProblemaUsuarioViewSet, EscolaDashboardView

router = routers.DefaultRouter()
router.register(r'lacunas', LacunaViewSet, basename='lacunas')
router.register(r'problemas-usuario', ProblemaUsuarioViewSet, basename='problemas-usuario')

urlpatterns = router.urls


from django.urls import path
from . import views

urlpatterns = [
    path('escola/dashboard/', views.EscolaDashboardView.as_view(), name='escola_dashboard'),
    path('dashboard/', views.problema_dashboard_view, name='problemas'),
    path('relatar-problema/', views.relatar_problema_view, name='relatar_problema'),
]

