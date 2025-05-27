from rest_framework import routers
from .views import LacunaViewSet, ProblemaUsuarioViewSet

router = routers.DefaultRouter()
router.register(r'lacunas', LacunaViewSet, basename='lacunas')
router.register(r'problemas-usuario', ProblemaUsuarioViewSet, basename='problemas-usuario')

urlpatterns = router.urls


from django.urls import path
from . import views

urlpatterns = [
    path('escola/dashboard/', views.problema_dashboard_view, name='problema_dashboard'),
]

