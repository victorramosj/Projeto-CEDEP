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
    """
    ViewSet para o CRUD de Camas.
    Permite criar, listar, atualizar e excluir camas.
    Possui busca pela identificação da cama.
    """
    queryset = Cama.objects.all()
    serializer_class = CamaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['identificacao']


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

# reservas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Quarto, Cama, Hospede, Reserva
from .forms import QuartoForm, CamaForm, HospedeForm, ReservaForm

# Views para gerenciamento (listagem) dos registros

def gerenciar_quartos(request):
    quartos = Quarto.objects.all()
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    context = {
        'quartos': quartos,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'reservas/gerenciar_quartos.html', context)


def gerenciar_camas(request):
    camas = Cama.objects.all()
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    context = {
        'camas': camas,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'reservas/gerenciar_camas.html', context)


def gerenciar_hospedes(request):
    hospedes = Hospede.objects.all()
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
    context = {
        'hospedes': hospedes,
        'query': query,
        'filter_by': filter_by,
    }
    return render(request, 'reservas/gerenciar_hospedes.html', context)


def gerenciar_reservas(request):
    reservas = Reserva.objects.all()
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')
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


def hospede_form(request, pk=None):
    """ Cria ou edita um Hóspede. """
    if pk:
        hospede = get_object_or_404(Hospede, pk=pk)
    else:
        hospede = None

    if request.method == 'POST':
        form = HospedeForm(request.POST, instance=hospede)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_hospedes')
    else:
        form = HospedeForm(instance=hospede)

    context = {'form': form, 'hospede': hospede}
    return render(request, 'reservas/hospede_form.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from .forms import ReservaForm
from .models import Reserva

def reserva_form(request, pk=None):
    """ Cria ou edita uma Reserva. """
    if pk:
        reserva = get_object_or_404(Reserva, pk=pk)
    else:
        reserva = None

    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_reservas')
    else:
        form = ReservaForm(instance=reserva)

    context = {'form': form, 'reserva': reserva}
    return render(request, 'reservas/reserva_form.html', context)

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