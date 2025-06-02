from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Quarto, Cama, Hospede, Reserva
from .serializers import QuartoSerializer, CamaSerializer, HospedeSerializer, ReservaSerializer


class QuartoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o CRUD de Quartos.
    Permite criar, listar, atualizar e excluir quartos.
    Possui busca por número ou descrição.
    """
    queryset = Quarto.objects.all()
    serializer_class = QuartoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['numero', 'descricao']


class CamaViewSet(viewsets.ModelViewSet):
    queryset = Cama.objects.all()
    serializer_class = CamaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['quarto']
    search_fields = ['identificacao']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context


class HospedeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o CRUD de Hóspedes.
    Permite criar, listar, atualizar e excluir hóspedes.
    Possui busca por nome, CPF ou e-mail.
    """
    queryset = Hospede.objects.all()
    serializer_class = HospedeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'cpf', 'email']


from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Quarto, Cama, Hospede, Reserva, Ocupacao
from .serializers import QuartoSerializer, CamaSerializer, HospedeSerializer, ReservaSerializer, OcupacaoSerializer

class ReservaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o CRUD de Reservas.
    Agora a reserva envolve apenas informações do hóspede, datas e status.
    """
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['hospede', 'status']
    search_fields = ['hospede__nome', 'status']

    def perform_destroy(self, instance):
        instance.delete()

class OcupacaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o CRUD de Ocupações.
    Gerencia o controle de quartos e camas ocupadas.
    """
    queryset = Ocupacao.objects.all()
    serializer_class = OcupacaoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['hospede', 'cama', 'status']
    search_fields = ['hospede__nome', 'cama__identificacao', 'status']
    
    def perform_create(self, serializer):
        # Ao criar uma ocupação ATIVA, atualiza o status da cama
        ocupacao = serializer.save()
        if ocupacao.status == 'ATIVA':
            ocupacao.cama.status = 'OCUPADA'
            ocupacao.cama.save()

# reservas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Quarto, Cama, Hospede, Reserva
from .forms import QuartoForm, CamaForm, HospedeForm, ReservaForm

# Configuração comum de paginação
ITENS_POR_PAGINA = 10

def gerenciar_quartos(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    # Filtragem básica
    quartos_list = Quarto.objects.all()
    
    if query:
        quartos_list = quartos_list.filter(numero__icontains=query)
    
    # Paginação
    paginator = Paginator(quartos_list, ITENS_POR_PAGINA)
    
    try:
        quartos = paginator.page(page_number)
    except PageNotAnInteger:
        quartos = paginator.page(1)
    except EmptyPage:
        quartos = paginator.page(paginator.num_pages)

    context = {
        'quartos': quartos,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'reservas/gerenciar_quartos.html', context)

def gerenciar_camas(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    camas_list = Cama.objects.select_related('quarto').all()
    quartos = Quarto.objects.all().order_by('numero')  # Lista os quartos disponíveis

    if query:
        if filter_by == 'identificacao':
            camas_list = camas_list.filter(identificacao__icontains=query)
        elif filter_by == 'quarto':
            try:
                query = int(query)  # Certifique-se de que é um número
                camas_list = camas_list.filter(quarto__numero=query)
            except ValueError:
                camas_list = Cama.objects.none()  # Retorna lista vazia se a conversão falhar
        elif filter_by == 'status':
            camas_list = camas_list.filter(status=query)

    paginator = Paginator(camas_list, 10)  
    camas = paginator.get_page(page_number)

    return render(request, 'reservas/gerenciar_camas.html', {
        'camas': camas,
        'quartos': quartos,
        'query': query,
        'filter_by': filter_by
    })

def gerenciar_hospedes(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    hospedes_list = Hospede.objects.all()
    
    if query:
        hospedes_list = hospedes_list.filter(
            Q(nome__icontains=query) |
            Q(cpf__icontains=query) |
            Q(email__icontains=query)
        )
    
    paginator = Paginator(hospedes_list, ITENS_POR_PAGINA)
    
    try:
        hospedes = paginator.page(page_number)
    except PageNotAnInteger:
        hospedes = paginator.page(1)
    except EmptyPage:
        hospedes = paginator.page(paginator.num_pages)

    context = {
        'hospedes': hospedes,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'reservas/gerenciar_hospedes.html', context)

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Quarto, Cama, Hospede, Reserva, Ocupacao
from .forms import QuartoForm, CamaForm, HospedeForm, ReservaForm, OcupacaoForm

ITENS_POR_PAGINA = 20


def gerenciar_reservas(request):
    # Parâmetros de consulta
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    # Base do queryset
    reservas_list = Reserva.objects.all()

    # Aplicar filtros antes da paginação
    if filter_by == 'hospede' and search:
        reservas_list = reservas_list.filter(hospede__nome__icontains=search)
    elif filter_by == 'status' and status_filter:
        reservas_list = reservas_list.filter(status__iexact=status_filter)
    elif filter_by == 'all' and search:
        reservas_list = reservas_list.filter(
            Q(hospede__nome__icontains=search) | Q(status__icontains=search)
        )

    # Ordenar do mais recente para o mais antigo
    reservas_list = reservas_list.order_by('-criado_em')

    # Paginação
    paginator = Paginator(reservas_list, ITENS_POR_PAGINA)
    try:
        reservas = paginator.page(page_number)
    except PageNotAnInteger:
        reservas = paginator.page(1)
    except EmptyPage:
        reservas = paginator.page(paginator.num_pages)

    # Contexto para o template
    context = {
        'reservas': reservas,
        'search': search,
        'status': status_filter,
        'filter_by': filter_by,
    }
    return render(request, 'reservas/gerenciar_reservas.html', context)

def reserva_form(request, pk=None):
    reserva = get_object_or_404(Reserva, pk=pk) if pk else None

    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_reservas')
    else:
        form = ReservaForm(instance=reserva)
    
    context = {
        'form': form,
        'reserva': reserva,
    }
    return render(request, 'reservas/reserva_form.html', context)

# Views para criação e edição (Formulários)

def quarto_form(request, pk=None):
    """ Cria ou edita um Quarto. """
    if pk:
        quarto = get_object_or_404(Quarto, pk=pk)
    else:
        quarto = None

    if request.method == 'POST':
        form = QuartoForm(request.POST, instance=quarto)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_quartos')
    else:
        form = QuartoForm(instance=quarto)

    context = {'form': form, 'quarto': quarto}
    return render(request, 'reservas/quarto_form.html', context)


def cama_form(request, pk=None):
    """ Cria ou edita uma Cama. """
    if pk:
        cama = get_object_or_404(Cama, pk=pk)
    else:
        cama = None

    if request.method == 'POST':
        form = CamaForm(request.POST, instance=cama)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_camas')
    else:
        form = CamaForm(instance=cama)

    context = {'form': form, 'cama': cama}
    return render(request, 'reservas/cama_form.html', context)

from django.template.loader import render_to_string
def hospede_form(request, pk=None):
    hospede = get_object_or_404(Hospede, pk=pk) if pk else None
    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = HospedeForm(request.POST, instance=hospede)
        if form.is_valid():
            novo_hospede = form.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'hospede_id': novo_hospede.id,
                    'nome': novo_hospede.nome,  # inclua o nome para atualizar o select
                    'message': 'Hóspede salvo com sucesso!'
                })
            
            if next_url:
                return redirect(next_url)
            return redirect('gerenciar_hospedes')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'form_html': render_to_string('reservas/hospede_form_modal.html', {
                    'form': form
                }, request=request)
            }, status=400)
    else:
        form = HospedeForm(instance=hospede)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'form_html': render_to_string('reservas/hospede_form_modal.html', {
                'form': form,
                'next': next_url
            }, request=request)
        })

    return render(request, 'reservas/hospede_form.html', {
        'form': form,
        'hospede': hospede
    })


def listar_hospedes_json(request):
    hospedes = Hospede.objects.all().values('id', 'nome')
    return JsonResponse(list(hospedes), safe=False)

def gerenciar_ocupacoes(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    ocupacoes_list = Ocupacao.objects.select_related('hospede', 'cama').all()
    
    if query:
        ocupacoes_list = ocupacoes_list.filter(
            Q(hospede__nome__icontains=query) |
            Q(cama__identificacao__icontains=query)
        )
    
    if filter_by != 'all':
        ocupacoes_list = ocupacoes_list.filter(status=filter_by)
    
    paginator = Paginator(ocupacoes_list, ITENS_POR_PAGINA)
    
    try:
        ocupacoes = paginator.page(page_number)
    except PageNotAnInteger:
        ocupacoes = paginator.page(1)
    except EmptyPage:
        ocupacoes = paginator.page(paginator.num_pages)

    context = {
        'ocupacoes': ocupacoes,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'reservas/gerenciar_ocupacoes.html', context)

def ocupacao_form(request, pk=None):
    ocupacao = get_object_or_404(Ocupacao, pk=pk) if pk else None
    quartos = Quarto.objects.all()
    
    # Captura os parâmetros da URL
    quarto_id = request.GET.get('quarto')
    cama_id = request.GET.get('cama')
    
    # Obter o objeto Cama se cama_id existir
    cama_selecionada_obj = None
    if cama_id:
        try:
            cama_selecionada_obj = Cama.objects.get(id=cama_id)
        except Cama.DoesNotExist:
            pass
    
    initial = {}
    if not ocupacao:
        if quarto_id:
            initial['quarto'] = int(quarto_id)
        if cama_id:
            initial['cama'] = int(cama_id)
    
    if request.method == 'POST':
        form = OcupacaoForm(request.POST, instance=ocupacao)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_ocupacoes')
    else:
        form = OcupacaoForm(instance=ocupacao, initial=initial)
    
    context = {
        'form': form,
        'ocupacao': ocupacao,
        'quartos': quartos,
        'quarto_selecionado': ocupacao.cama.quarto.id if ocupacao else quarto_id,
        'cama_selecionada': ocupacao.cama.id if ocupacao else cama_id,
        'cama_selecionada_obj': cama_selecionada_obj  # Novo
    }
    return render(request, 'reservas/ocupacoes_form.html', context)



# views.py
from django.http import JsonResponse
from .models import Cama

def camas_disponiveis(request):
    quarto_id = request.GET.get('quarto')
    try:
        camas = Cama.objects.filter(
            quarto__id=quarto_id,
            status='DISPONIVEL'
        )
        
        data = [{
            'id': cama.id,
            'identificacao': cama.identificacao,
            'status': cama.status
        } for cama in camas]
        
        return JsonResponse({'camas': data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

from django.shortcuts import render
from django.db.models import Count, Q
from .models import Quarto, Cama, Hospede, Reserva
from datetime import date

def dashboard(request):
    # Estatísticas básicas
    total_quartos = Quarto.objects.count()
    total_camas = Cama.objects.count()
    total_hospedes = Hospede.objects.count()
    # Para reservas, consideramos "confirmadas" como ativas
    reservas_ativas = Reserva.objects.filter(status='CONFIRMADA').count()
    
    # Status das camas: considere que o primeiro item (DISPONIVEL) e o segundo (OCUPADA)
    status_camas = Cama.objects.values('status').annotate(total=Count('id'))
    # Ordena de forma que 'DISPONIVEL' venha primeiro (ajuste conforme necessidade)
    status_camas = sorted(status_camas, key=lambda x: x['status'])
    
    # Reservas recentes: sem relação com quarto ou cama
    recent_reservations = Reserva.objects.select_related('hospede').order_by('-criado_em')[:5]
    
    # Reservas por status
    reservas_status = Reserva.objects.values('status').annotate(total=Count('id'))
    
    # Conversão dos dados para gráficos
    camas_labels = [item['status'] for item in status_camas]
    camas_data = [item['total'] for item in status_camas]
    
    reservas_labels = [item['status'] for item in reservas_status]
    reservas_data = [item['total'] for item in reservas_status]
    
    context = {
        'total_quartos': total_quartos,
        'total_camas': total_camas,
        'total_hospedes': total_hospedes,
        'reservas_ativas': reservas_ativas,
        'recent_reservations': recent_reservations,
        'camas_labels': camas_labels,
        'camas_data': camas_data,
        'reservas_labels': reservas_labels,
        'reservas_data': reservas_data,
    }
    
    return render(request, 'reservas/dashboard.html', context)

def mapa_interativo(request):
    hospedes = Hospede.objects.all()
    context = {
        'hospedes': hospedes
    }
    return render(request, 'reservas/mapa_interativo.html', context)

from django.db.models.functions import ExtractYear, ExtractMonth
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from .models import Reserva, Ocupacao

def gerar_contexto_comum():
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    # Retorna lista de tuplas: [(1, 'Janeiro'), (2, 'Fevereiro'), ...]
    meses_com_indices = list(enumerate(meses, start=1))
    return {
        'meses': meses_com_indices,
        'now': datetime.now()
    }

def reservas_report_pdf(request):
    if request.method == 'POST':
        tipo_filtro = request.POST.get('tipo_filtro')
        data_inicio = data_fim = None

        if tipo_filtro == 'mes':
            mes = int(request.POST.get('mes'))
            ano = int(request.POST.get('ano'))
            data_inicio = datetime(ano, mes, 1)
            data_fim = datetime(ano + (1 if mes == 12 else 0), (mes % 12) + 1, 1)
        elif tipo_filtro == 'periodo':
            data_inicio = datetime.strptime(request.POST.get('data_inicio'), '%Y-%m-%d')
            data_fim = datetime.strptime(request.POST.get('data_fim'), '%Y-%m-%d')

        reservas = Reserva.objects.filter(
            data_checkin__gte=data_inicio, 
            data_checkout__lte=data_fim
        ).order_by('data_checkin')

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_reservas_{datetime.now().date()}.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        p.setFont("Helvetica-Bold", 16)
        p.drawString(2 * cm, height - 2 * cm, "Relatório de Reservas - CEDEPE GRE Floresta")
        
        criar_cabecalho(p, height, data_inicio, data_fim)
        criar_corpo_reservas(p, reservas, height)
        
        p.save()
        return response

    context = gerar_contexto_comum()
    return render(request, 'relatorios/filtro_reservas.html', context)


def ocupacoes_report_pdf(request):
    if request.method == 'POST':
        tipo_filtro = request.POST.get('tipo_filtro')
        data_inicio = data_fim = None

        if tipo_filtro == 'mes':
            mes = int(request.POST.get('mes'))
            ano = int(request.POST.get('ano'))
            data_inicio = datetime(ano, mes, 1)
            data_fim = datetime(ano + (1 if mes == 12 else 0), (mes % 12) + 1, 1)
        elif tipo_filtro == 'periodo':
            data_inicio = datetime.strptime(request.POST.get('data_inicio'), '%Y-%m-%d')
            data_fim = datetime.strptime(request.POST.get('data_fim'), '%Y-%m-%d')

        ocupacoes = Ocupacao.objects.filter(
            data_checkin__gte=data_inicio, 
            data_checkout__lte=data_fim
        ).order_by('data_checkin')

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_ocupacoes_{datetime.now().date()}.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        p.setFont("Helvetica-Bold", 16)
        p.drawString(2 * cm, height - 2 * cm, "Relatório de Ocupações - CEDEPE GRE Floresta")
        
        criar_cabecalho(p, height, data_inicio, data_fim)
        criar_corpo_ocupacoes(p, ocupacoes, height)
        
        p.save()
        return response

    context = gerar_contexto_comum()
    return render(request, 'relatorios/filtro_ocupacoes.html', context)


def criar_cabecalho(p, height, data_inicio, data_fim):
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2 * cm, height - 2.7 * cm, f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    p.setStrokeColorRGB(0.2, 0.2, 0.2)
    p.setLineWidth(0.5)
    p.line(2 * cm, height - 2.9 * cm, 19 * cm, height - 2.9 * cm)

def criar_corpo_reservas(p, reservas, height):
    y = height - 4 * cm
    page_num = 1
    for i, reserva in enumerate(reservas, start=1):
        if y < 4 * cm:
            p.setFont("Helvetica", 9)
            p.drawString(2 * cm, 2 * cm, f"Página {page_num}")
            p.showPage()
            page_num += 1
            criar_cabecalho(p, height, reserva.data_checkin, reserva.data_checkout)
            y = height - 4 * cm

        p.setFont("Helvetica-Bold", 10)
        p.drawString(2 * cm, y, f"Hóspede: {reserva.hospede.nome} ")
        y -= 0.5 * cm
        p.setFont("Helvetica-Bold", 8)
        p.drawString(2 * cm, y, f"Innstituicao: {reserva.hospede.instituicao}")
        p.setFont("Helvetica", 10)
        y -= 0.5 * cm
        p.drawString(2.5 * cm, y, f"Check-in: {reserva.data_checkin.strftime('%d/%m/%Y')}")
        y -= 0.5 * cm
        p.drawString(2.5 * cm, y, f"Check-out: {reserva.data_checkout.strftime('%d/%m/%Y')}")
        y -= 0.5 * cm
        p.drawString(2.5 * cm, y, f"Status: {reserva.get_status_display()}")

        y -= 0.4 * cm
        p.setStrokeColorRGB(0.8, 0.8, 0.8)
        p.setLineWidth(0.2)
        p.line(2 * cm, y, 19 * cm, y)
        y -= 0.4 * cm

    p.setFont("Helvetica", 9)
    p.drawString(2 * cm, 2 * cm, f"Página {page_num}")


def criar_corpo_ocupacoes(p, ocupacoes, height):
    y = height - 4 * cm
    page_num = 1
    for i, ocupacao in enumerate(ocupacoes, start=1):
        if y < 4 * cm:
            p.setFont("Helvetica", 9)
            p.drawString(2 * cm, 2 * cm, f"Página {page_num}")
            p.showPage()
            page_num += 1
            criar_cabecalho(p, height, ocupacao.data_checkin, ocupacao.data_checkout)
            y = height - 4 * cm

        p.setFont("Helvetica-Bold", 10)
        p.drawString(2 * cm, y, f"Hóspede: {ocupacao.hospede.nome}")
        y -= 0.5 * cm
        p.setFont("Helvetica-Bold", 8)
        p.drawString(2 * cm, y, f"Instituição:  {ocupacao.hospede.instituicao}")
        p.setFont("Helvetica", 10)
        y -= 0.5 * cm
        p.drawString(2.5 * cm, y, f"Cama: {ocupacao.cama.identificacao}")
        y -= 0.5 * cm
        p.drawString(2.5 * cm, y, f"Check-in: {ocupacao.data_checkin.strftime('%d/%m/%Y')}")
        y -= 0.5 * cm
        p.drawString(2.5 * cm, y, f"Check-out: {ocupacao.data_checkout.strftime('%d/%m/%Y')}")
        y -= 0.5 * cm
        p.drawString(2.5 * cm, y, f"Status: {ocupacao.get_status_display()}")

        y -= 0.4 * cm
        p.setStrokeColorRGB(0.8, 0.8, 0.8)
        p.setLineWidth(0.2)
        p.line(2 * cm, y, 19 * cm, y)
        y -= 0.4 * cm

    p.setFont("Helvetica", 9)
    p.drawString(2 * cm, 2 * cm, f"Página {page_num}")
