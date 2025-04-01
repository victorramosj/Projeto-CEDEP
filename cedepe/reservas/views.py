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


class ReservaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o CRUD de Reservas.
    Permite criar, listar, atualizar e excluir reservas.
    É possível filtrar por hóspede, quarto (através da cama) e status da reserva.
    """
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['hospede', 'cama__quarto', 'status']
    search_fields = ['hospede__nome', 'cama__quarto__numero', 'status']

    def perform_destroy(self, instance):
        cama = instance.cama
        cama.status = 'DISPONIVEL'
        cama.save()
        instance.delete()

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

    camas_list = Cama.objects.all()
    
    if query:
        camas_list = camas_list.filter(
            Q(identificacao__icontains=query) |
            Q(quarto__numero__icontains=query)
        )
    
    if filter_by != 'all':
        camas_list = camas_list.filter(status=filter_by)
    
    paginator = Paginator(camas_list, ITENS_POR_PAGINA)
    
    try:
        camas = paginator.page(page_number)
    except PageNotAnInteger:
        camas = paginator.page(1)
    except EmptyPage:
        camas = paginator.page(paginator.num_pages)

    context = {
        'camas': camas,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'reservas/gerenciar_camas.html', context)

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

def gerenciar_reservas(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    page_number = request.GET.get('page')

    reservas_list = Reserva.objects.all()
    
    if query:
        reservas_list = reservas_list.filter(
            Q(hospede__nome__icontains=query) |
            Q(cama__identificacao__icontains=query) |
            Q(cama__quarto__numero__icontains=query)
        )
    
    if filter_by != 'all':
        reservas_list = reservas_list.filter(status=filter_by)
    
    paginator = Paginator(reservas_list, ITENS_POR_PAGINA)
    
    try:
        reservas = paginator.page(page_number)
    except PageNotAnInteger:
        reservas = paginator.page(1)
    except EmptyPage:
        reservas = paginator.page(paginator.num_pages)

    context = {
        'reservas': reservas,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'reservas/gerenciar_reservas.html', context)

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

from datetime import date
from django.shortcuts import get_object_or_404, redirect, render
# Certifique-se de importar os modelos e formulários necessários:
from .models import Quarto, Cama, Reserva
from .forms import ReservaForm

def reserva_form(request, pk=None):
    reserva = None
    quarto_selecionado = None
    cama_selecionada_obj = None

    # Verifica se veio cama por query parameter
    cama_id_param = request.GET.get('cama')
    if cama_id_param:
        cama_selecionada_obj = get_object_or_404(Cama, pk=cama_id_param)
        quarto_selecionado = cama_selecionada_obj.quarto.id

    # Se for edição, carrega a reserva
    if pk:
        reserva = get_object_or_404(Reserva, pk=pk)
        cama_selecionada_obj = reserva.cama
        quarto_selecionado = reserva.cama.quarto.id

    # Recupera todos os quartos para preencher o select
    quartos = Quarto.objects.all()

    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            reserva = form.save(commit=False)
            # Aqui, decidimos se a cama deve ser considerada ocupada de acordo com as datas da reserva.
            # Se a reserva estiver ATIVA e a data de check-in for hoje ou anterior e
            # a data de check-out for futura, então a cama passa a ser ocupada.
            if reserva.status == 'ATIVA':
                hoje = date.today()
                if reserva.data_checkin <= hoje < reserva.data_checkout:
                    reserva.cama.status = 'OCUPADA'
                else:
                    # Se a reserva é para data futura (ou já passou a data de checkout), 
                    # mantemos a cama como disponível.
                    reserva.cama.status = 'DISPONIVEL'
                reserva.cama.save()
            reserva.save()
            return redirect('mapa_interativo')
        else:
            # Recupera seleções do POST para manter estado
            quarto_selecionado = request.POST.get('quarto')
            cama_id_post = request.POST.get('cama')
            try:
                cama_selecionada_obj = Cama.objects.get(pk=cama_id_post)
            except (Cama.DoesNotExist, ValueError):
                cama_selecionada_obj = None
    else:
        # Se não for POST, inicializa o formulário com a cama selecionada, se houver
        form = ReservaForm(instance=reserva, initial={'cama': cama_selecionada_obj.id if cama_selecionada_obj else None})

    # Se for POST e o formulário não for válido, recria o formulário mantendo o estado inicial
    if request.method == 'POST' and not form.is_valid():
        form = ReservaForm(request.POST, instance=reserva, initial={'cama': cama_selecionada_obj.id if cama_selecionada_obj else None})

    context = {
        'form': form,
        'reserva': reserva,
        'quartos': quartos,
        'quarto_selecionado': quarto_selecionado,
        'cama_selecionada': cama_selecionada_obj.id if cama_selecionada_obj else None
    }
    return render(request, 'reservas/reserva_form.html', context)



from django.http import JsonResponse
from .models import Cama

def camas_disponiveis(request):
    quarto_id = request.GET.get('quarto')
    try:
        camas = Cama.objects.filter(
            quarto__id=quarto_id,
            status='DISPONIVEL'
        ).prefetch_related('reserva_set')
        
        serializer = CamaSerializer(camas, many=True)
        return JsonResponse({
            'camas': serializer.data
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

# reservas/views.py
from django.shortcuts import render
from django.db.models import Count, Q
from .models import Quarto, Cama, Hospede, Reserva
from datetime import date

def dashboard(request):
    # Estatísticas básicas
    total_quartos = Quarto.objects.count()
    total_camas = Cama.objects.count()
    total_hospedes = Hospede.objects.count()
    reservas_ativas = Reserva.objects.filter(status='ATIVA').count()
    
    # Status das camas
    status_camas = Cama.objects.values('status').annotate(total=Count('id'))
    
    # Reservas recentes
    recent_reservations = Reserva.objects.select_related('hospede', 'cama').order_by('-criado_em')[:5]
    
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