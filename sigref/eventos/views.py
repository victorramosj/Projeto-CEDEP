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
    

from django.db.models import Q

# Views para Agendamentos
def gerenciar_agendamentos(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    agendamentos_list = Agendamento.objects.all()
    
    if query:
        agendamentos_list = agendamentos_list.filter(
            Q(evento__titulo__icontains=query) |
            Q(salas__nome__icontains=query)
        ).distinct()
    
    # Ordena do mais recente para o mais antigo
    agendamentos_list = agendamentos_list.order_by('-inicio')
    
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
    filterset_fields = ['salas', 'evento']
    search_fields = ['evento__descricao']

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
        
        if request.query_params.get('format') == 'fullcalendar':
            data = [{
                'id': agendamento.id,
                'title': agendamento.evento.titulo,
                'start': timezone.localtime(agendamento.inicio).isoformat(),
                'end': timezone.localtime(agendamento.fim).isoformat(),
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
    agendamentos_por_sala = Sala.objects.annotate(total=Count('agendamentos')).filter(total__gt=0)
    salas_labels = [sala.nome for sala in agendamentos_por_sala]
    salas_data = [sala.total for sala in agendamentos_por_sala]

    
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


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from .models import Agendamento
from django.utils import timezone

class FullCalendarEventsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        agendamentos = Agendamento.objects.all()
        events = [{
            'id': agendamento.id,
            'title': agendamento.evento.titulo,
            'start': timezone.localtime(agendamento.inicio).isoformat(),
            'end': timezone.localtime(agendamento.fim).isoformat(),
            'extendedProps': {
                'salas': [sala.nome for sala in agendamento.salas.all()],
                'descricao': agendamento.evento.descricao,
                'horario': f"{timezone.localtime(agendamento.inicio).strftime('%H:%M')} - {timezone.localtime(agendamento.fim).strftime('%H:%M')}"
            }
        } for agendamento in agendamentos]
        return Response(events)

    
from django.db.models.functions import ExtractYear    
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
from .models import Evento, Agendamento
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph  # Import corrigido aqui



def eventos_report_pdf(request):
    if request.method == 'POST':
        tipo_filtro = request.POST.get('tipo_filtro')
        data_inicio = data_fim = None

        if tipo_filtro == 'mes':
            mes = int(request.POST.get('mes'))
            ano = int(request.POST.get('ano'))
            data_inicio = datetime(ano, mes, 1)
            if mes == 12:
                data_fim = datetime(ano + 1, 1, 1)
            else:
                data_fim = datetime(ano, mes + 1, 1)
        elif tipo_filtro == 'periodo':
            data_inicio = datetime.strptime(request.POST.get('data_inicio'), '%Y-%m-%d')
            data_fim = datetime.strptime(request.POST.get('data_fim'), '%Y-%m-%d')

        agendamentos = Agendamento.objects.filter(inicio__gte=data_inicio, fim__lte=data_fim).order_by('inicio')

        # Geração do PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_eventos_{datetime.now().date()}.pdf"'

        styles = {
            'title': ParagraphStyle(
                name='Title',
                fontSize=16,
                leading=18,
                textColor=HexColor('#2c3e50'),
                fontName='Helvetica-Bold',
                spaceAfter=12
            ),
            'header': ParagraphStyle(
                name='Header',
                fontSize=10,
                textColor=HexColor('#7f8c8d'),
                fontName='Helvetica',
                spaceAfter=15
            ),
            'event_title': ParagraphStyle(
                name='EventTitle',
                fontSize=12,
                textColor=HexColor('#2c3e50'),
                fontName='Helvetica-Bold',
                spaceAfter=6
            ),
            'detail': ParagraphStyle(
                name='Detail',
                fontSize=10,
                textColor=HexColor('#34495e'),
                fontName='Helvetica',
                leading=12,
                spaceAfter=8
            )
        }

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        margin = 2 * cm
        line_height = 0.7 * cm
        max_width = width - 2 * margin

        # Cabeçalho
        title = Paragraph("Relatório de Eventos e Agendamentos", styles['title'])
        title.wrapOn(p, width, height)
        title.drawOn(p, margin, height - margin)

        period_text = f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
        period = Paragraph(period_text, styles['header'])
        period.wrapOn(p, width, height)
        period.drawOn(p, margin, height - margin - 1.2*cm)

        y = height - margin - 3*cm
        for agendamento in agendamentos:
            if y < 6 * cm:  # Mais espaço reservado para "card"
                p.showPage()
                y = height - margin
                title.drawOn(p, margin, height - margin)
                period.drawOn(p, margin, height - margin - 1.2*cm)
                y -= 2*cm

            evento = agendamento.evento

            # Define cor de fundo com base na hora
            hora_inicio = agendamento.inicio.hour
            if hora_inicio < 12:
                bg_color = HexColor('#dff9fb')  # manhã
            elif hora_inicio < 18:
                bg_color = HexColor('#f6e58d')  # tarde
            else:
                bg_color = HexColor('#ffbe76')  # noite

            card_height = 5 * cm
            card_width = max_width

            # Desenha o retângulo (card)
            p.setFillColor(bg_color)
            p.roundRect(margin, y - card_height, card_width, card_height, 10, fill=True, stroke=False)

            # Adiciona título do evento
            event_title = Paragraph(f"<b>Evento:</b> {evento.titulo}", styles['event_title'])
            event_title.wrapOn(p, card_width - 1*cm, line_height)
            event_title.drawOn(p, margin + 0.5*cm, y - 0.8*cm)

            # Detalhes do agendamento
            details = [
            f"<b>Início:</b> {agendamento.inicio.strftime('%d/%m/%Y %H:%M')} | Fim:</b> {agendamento.fim.strftime('%d/%m/%Y %H:%M')}",
            f"<b>Organizador:</b> {evento.organizador} | ",
            f"<b>Participantes:</b> {agendamento.participantes or 'Não informado'}",
            f"<b>Salas:</b> {', '.join([s.nome for s in agendamento.salas.all()])}"
        ]

            text_y = y - 1.6*cm
            for detail in details:
                text = Paragraph(detail, styles['detail'])
                text.wrapOn(p, card_width - 1.5*cm, line_height)
                text.drawOn(p, margin + 0.7*cm, text_y)
                text_y -= line_height

            y -= card_height + 0.5*cm

        p.save()
        return response

    # Gera lista de meses
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    # Obtém anos distintos a partir dos agendamentos
    anos_inicio = Agendamento.objects.annotate(ano=ExtractYear('inicio')).values_list('ano', flat=True)
    anos_fim = Agendamento.objects.annotate(ano=ExtractYear('fim')).values_list('ano', flat=True)
    anos = sorted(set(anos_inicio).union(anos_fim))

    return render(request, 'relatorios/filtro_eventos.html', {
        'meses': meses,
        'anos': anos,
    })

