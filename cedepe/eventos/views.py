from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from .models import Sala, Evento, Agendamento
from .forms import SalaForm, EventoForm, AgendamentoForm
from django.db.models import Q

ITENS_POR_PAGINA = 10

# Views para Salas
def gerenciar_salas(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    salas_list = Sala.objects.all()
    
    if query:
        salas_list = salas_list.filter(
            Q(nome__icontains=query) |
            Q(localizacao__icontains=query)
        )
    
    paginator = Paginator(salas_list, ITENS_POR_PAGINA)
    
    try:
        salas = paginator.page(page_number)
    except PageNotAnInteger:
        salas = paginator.page(1)
    except EmptyPage:
        salas = paginator.page(paginator.num_pages)

    context = {
        'salas': salas,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'eventos/gerenciar_salas.html', context)

def sala_form(request, pk=None):
    sala = get_object_or_404(Sala, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_salas')
    else:
        form = SalaForm(instance=sala)
    
    context = {'form': form, 'sala': sala}
    return render(request, 'eventos/sala_form.html', context)

# Views para Eventos
def gerenciar_eventos(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    eventos_list = Evento.objects.all()
    
    if query:
        eventos_list = eventos_list.filter(
            Q(titulo__icontains=query) |
            Q(organizador__icontains=query)
        )
    
    paginator = Paginator(eventos_list, ITENS_POR_PAGINA)
    
    try:
        eventos = paginator.page(page_number)
    except PageNotAnInteger:
        eventos = paginator.page(1)
    except EmptyPage:
        eventos = paginator.page(paginator.num_pages)

    context = {
        'eventos': eventos,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'eventos/gerenciar_eventos.html', context)

def evento_form(request, pk=None):
    evento = None
    if pk:
        evento = get_object_or_404(Evento, pk=pk)
    
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('gerenciar_eventos')
    else:
        form = EventoForm(instance=evento)
    
    return render(request, 'eventos/evento_form.html', {
        'form': form,
        'evento': evento
    })
    

# Views para Agendamentos
def gerenciar_agendamentos(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    agendamentos_list = Agendamento.objects.all()
    
    if query:
        agendamentos_list = agendamentos_list.filter(
            Q(evento__titulo__icontains=query) |
            Q(sala__nome__icontains=query)
        )
    
    paginator = Paginator(agendamentos_list, ITENS_POR_PAGINA)
    
    try:
        agendamentos = paginator.page(page_number)
    except PageNotAnInteger:
        agendamentos = paginator.page(1)
    except EmptyPage:
        agendamentos = paginator.page(paginator.num_pages)

    context = {
        'agendamentos': agendamentos,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'eventos/gerenciar_agendamentos.html', context)

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Agendamento
from .forms import AgendamentoForm

def agendamento_form(request, pk=None):
    agendamento = get_object_or_404(Agendamento, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = AgendamentoForm(request.POST, instance=agendamento)
        if form.is_valid():
            form.save()
            return redirect('dashboard_eventos')
        else:
            # Adiciona mensagens de erro para cada campo inválido
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo {field}: {error}")
    else:
        form = AgendamentoForm(instance=agendamento)
    
    context = {'form': form, 'agendamento': agendamento}
    return render(request, 'eventos/agendamento_form.html', context)

# views.py (parte da API)
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Sala, Evento, Agendamento
from .serializers import SalaSerializer, EventoSerializer, AgendamentoSerializer

class SalaViewSet(viewsets.ModelViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'localizacao']

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['titulo', 'organizador']

class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['sala', 'evento']
    search_fields = ['evento__descricao']  # Ajustado para buscar pela descrição do evento

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Formato específico para FullCalendar
        if request.query_params.get('format') == 'fullcalendar':
            data = [{
                'id': agendamento.id,
                'title': agendamento.evento.titulo,
                'start': agendamento.inicio.isoformat(),
                'end': agendamento.fim.isoformat(),
                'extendedProps': {
                    'sala': agendamento.sala.nome,
                    'descricao': agendamento.evento.descricao
                }
            } for agendamento in queryset]
            return Response(data)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

from django.utils import timezone
from django.shortcuts import render
from django.db.models import Count
from .models import Evento, Agendamento, Sala

def dashboard(request):
    total_eventos = Evento.objects.count()
    total_agendamentos = Agendamento.objects.count()
    total_salas = Sala.objects.count()
    # Agendamentos próximos: que ainda não iniciaram (ou em andamento, dependendo da lógica)
    upcoming_agendamentos = Agendamento.objects.filter(inicio__gte=timezone.now()).order_by('inicio')[:5]
    
    # Agendamentos por Sala para o gráfico
    agendamentos_por_sala = Agendamento.objects.values('sala__nome').annotate(total=Count('id'))
    salas_labels = [item['sala__nome'] for item in agendamentos_por_sala]
    salas_data = [item['total'] for item in agendamentos_por_sala]
    
    context = {
        'total_eventos': total_eventos,
        'total_agendamentos': total_agendamentos,
        'total_salas': total_salas,
        'upcoming_agendamentos': upcoming_agendamentos,
        'salas_labels': salas_labels,
        'salas_data': salas_data,
        'salas': Sala.objects.all(),    # para o form do modal
        'eventos': Evento.objects.all(),  # para o form do modal
    }
    
    return render(request, 'eventos/dashboard.html', context)

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Agendamento
from rest_framework import permissions

# views.py
class FullCalendarEventsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        agendamentos = Agendamento.objects.all()
        events = [{
            'id': agendamento.id,
            'title': agendamento.evento.titulo,
            'start': agendamento.inicio.isoformat(),
            'end': agendamento.fim.isoformat(),
            'extendedProps': {
                'sala': agendamento.sala.nome,
                'descricao': agendamento.evento.descricao,
                'horario': f"{agendamento.inicio.strftime('%H:%M')} - {agendamento.fim.strftime('%H:%M')}"  # Novo campo
            }
        } for agendamento in agendamentos]
        return Response(events)
