from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register(r'salas', views.SalaViewSet, basename='sala')
router.register(r'eventos', views.EventoViewSet, basename='evento')
router.register(r'agendamentos', views.AgendamentoViewSet, basename='agendamento')
urlpatterns = [
    path('api/', include(router.urls)),
    path('api/fullcalendar/', views.FullCalendarEventsView.as_view(), name='fullcalendar-events'),
    
    path('dashboard_eventos/', views.dashboard, name='dashboard_eventos'),
   # Salas
    path('salas/', views.gerenciar_salas, name='gerenciar_salas'),
    path('salas/nova/', views.sala_form, name='sala_form'),
    path('salas/editar/<int:pk>/', views.sala_form, name='editar_sala'),
    
    # Eventos
    path('eventos/', views.gerenciar_eventos, name='gerenciar_eventos'),
    path('eventos/novo/', views.evento_form, name='evento_form'),
    path('eventos/novo/modal', views.evento_form, name='evento_form_modal'),
    path('eventos/editar/<int:pk>/', views.evento_form, name='editar_evento'),
    
    # Agendamentos
    path('agendamentos/', views.gerenciar_agendamentos, name='gerenciar_agendamentos'),
    path('agendamentos/novo/', views.agendamento_form, name='agendamento_form'),
    path('agendamentos/editar/<int:pk>/', views.agendamento_form, name='editar_agendamento'),
    

]