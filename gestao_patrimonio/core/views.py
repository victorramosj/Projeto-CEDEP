from django.shortcuts import render
from django.db.models import Count, Sum
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import permission_classes
from datetime import date
from .models import Bem, Categoria, Departamento, Fornecedor, Movimentacao, LogAlteracao
from .serializers import (
    BemSerializer,
    CategoriaSerializer,
    DepartamentoSerializer,
    FornecedorSerializer,
    MovimentacaoSerializer,
)

# Viewsets da API
class BemViewSet(viewsets.ModelViewSet):
    queryset = Bem.objects.all()
    serializer_class = BemSerializer

class MovimentacaoViewSet(viewsets.ModelViewSet):
    queryset = Movimentacao.objects.all()
    serializer_class = MovimentacaoSerializer

# View para renderizar o dashboard
@login_required
def dashboard(request):
    total_bens = Bem.objects.count()
    total_valor = Bem.objects.aggregate(Sum('valor'))['valor__sum'] or 0
    categorias = Categoria.objects.annotate(qtd=Count('bem')).order_by('-qtd')[:5]

    # Monta um dicionário com contagem para cada status
    status_counts_qs = Bem.objects.values('status').annotate(count=Count('id'))
    status_counts = {'ativo': 0, 'manutencao': 0, 'descartado': 0}
    for item in status_counts_qs:
        status_counts[item['status']] = item['count']

    departamentos = Departamento.objects.annotate(qtd=Count('bem')).order_by('-qtd')[:5]
    recent_movements = Movimentacao.objects.select_related('bem', 'origem', 'destino')\
                            .order_by('-data_movimentacao')[:5]
    movimentacoes_hoje = Movimentacao.objects.filter(
        data_movimentacao__date=date.today()
    ).count()

    return render(request, 'core/dashboard.html', {
        'total_bens': total_bens,
        'total_valor': total_valor,
        'categorias': categorias,
        'status_counts': status_counts,
        'departamentos': departamentos,
        'recent_movements': recent_movements,
        'movimentacoes_hoje': movimentacoes_hoje,
    })


# View para renderizar o formulário de cadastro de Bem (HTML)
def bem_form_view(request):
    """Renderiza o template core/bem_form.html com as listas de Categoria, 
       Departamento e Fornecedor para preencher os selects."""
    categories = Categoria.objects.all()
    departments = Departamento.objects.all()
    suppliers = Fornecedor.objects.all()

    context = {
        'categories': categories,
        'departments': departments,
        'suppliers': suppliers
    }
    return render(request, 'core/bem_form.html', context)


from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

def gerenciar_bens(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', 'all')  # 'all' para pesquisar em todos os campos
    bens_list = Bem.objects.all()
    departamentos = Departamento.objects.all()

    if query:
        if filter_by == 'id':
            try:
                bens_list = bens_list.filter(id=int(query))
            except ValueError:
                bens_list = bens_list.none()
        elif filter_by == 'nome':
            bens_list = bens_list.filter(nome__icontains=query)
        elif filter_by == 'descricao':
            bens_list = bens_list.filter(descricao__icontains=query)
        elif filter_by == 'categoria':
            bens_list = bens_list.filter(categoria__nome__icontains=query)
        elif filter_by == 'departamento':
            bens_list = bens_list.filter(departamento__nome__icontains=query)
        elif filter_by == 'fornecedor':
            bens_list = bens_list.filter(fornecedor__nome__icontains=query)
        else:  # pesquisa geral em todos os campos
            bens_list = bens_list.filter(
                Q(nome__icontains=query) |
                Q(descricao__icontains=query) |
                Q(categoria__nome__icontains=query) |
                Q(departamento__nome__icontains=query) |
                Q(fornecedor__nome__icontains=query)
            )

    paginator = Paginator(bens_list, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    bens = paginator.get_page(page_number)

    context = {
        'bens': bens,
        'query': query,
        'filter_by': filter_by,
        'departamentos': departamentos,
        
    }
    return render(request, 'core/gerenciar_bens.html', context)
from django.http import JsonResponse
from .models import Bem

def buscar_tags_rfid(request):
    query = request.GET.get('q', '').strip()
    
    if query:
        tags = Bem.objects.filter(rfid_tag__icontains=query).order_by('rfid_tag')
        tags_list = list(tags.values('id', 'nome', 'rfid_tag', 'descricao', 'numero_patrimonio', 'departamento__nome'))
    else:
        tags_list = []
    
    return JsonResponse({'tags': tags_list})
from django.http import JsonResponse
from django.template.loader import render_to_string

def historico_item(request, bem_id):
    bem = get_object_or_404(Bem, id=bem_id)
    movimentacoes = Movimentacao.objects.filter(bem=bem)
    log_alteracoes = LogAlteracao.objects.filter(bem=bem)
    
    html = render_to_string('core/modals/historico_modal.html', {
        'movimentacoes': movimentacoes,
        'log_alteracoes': log_alteracoes,
        'bem': bem,
    })
    
    return JsonResponse({
        'html': html,
        'bem_nome': bem.nome
    })



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def criar_bem(request):
    if request.method == 'GET':
        return Response({"detail": "Use POST para enviar os dados."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    elif request.method == 'POST':
        serializer = BemSerializer(data=request.data)
        if serializer.is_valid():
            bem = serializer.save()
            # Cria um log de alteração para criação do bem
            descricao = f"Bem criado: {bem.nome}"
            LogAlteracao.objects.create(
                bem=bem,
                usuario=request.user,
                descricao=descricao
            )
            return Response({'success': True, 'id': bem.id, 'nome': bem.nome}, status=status.HTTP_201_CREATED)
        
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import status


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_categoria(request):
    serializer = CategoriaSerializer(data=request.data)
    if serializer.is_valid():
        categoria = serializer.save()
        return Response({'success': True, 'id': categoria.id, 'nome': categoria.nome}, status=status.HTTP_201_CREATED)
    error_messages = {field: error for field, error in serializer.errors.items()}
    return Response({'success': False, 'errors': error_messages}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_departamento(request):
    serializer = DepartamentoSerializer(data=request.data)
    if serializer.is_valid():
        departamento = serializer.save()
        return Response({'success': True, 'id': departamento.id, 'nome': departamento.nome}, status=status.HTTP_201_CREATED)
    error_messages = {field: error for field, error in serializer.errors.items()}
    return Response({'success': False, 'errors': error_messages}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_fornecedor(request):
    serializer = FornecedorSerializer(data=request.data)
    if serializer.is_valid():
        fornecedor = serializer.save()
        return Response({'success': True, 'id': fornecedor.id, 'nome': fornecedor.nome}, status=status.HTTP_201_CREATED)
    error_messages = {field: error for field, error in serializer.errors.items()}
    return Response({'success': False, 'errors': error_messages}, status=status.HTTP_400_BAD_REQUEST)

from django.db import models
from django.utils import formats
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import FieldDoesNotExist

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def editar_bem_api(request, pk):
    try:
        bem = Bem.objects.get(pk=pk)
    except Bem.DoesNotExist:
        return Response({'error': 'Bem não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = BemSerializer(bem, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 1. Capturar valores originais antes das alterações
    original_data = {}
    for field in serializer.validated_data.keys():
        try:
            original_data[field] = getattr(bem, field)
        except FieldDoesNotExist:
            continue

    # 2. Salvar as alterações
    serializer.save()

    # 3. Identificar e formatar mudanças
    descricao_lines = []
    for field, old_value in original_data.items():
        try:
            model_field = bem._meta.get_field(field)
            new_value = getattr(bem, field)
            
            if old_value != new_value:
                # Formatação especial para diferentes tipos de campos
                old_str, new_str = format_field_values(model_field, old_value, new_value)
                
                # Adiciona linha descritiva
                line = (
                    f"Campo '{model_field.verbose_name}' "
                    f"alterado de '{old_str}' para '{new_str}'"
                )
                descricao_lines.append(line)
                
        except FieldDoesNotExist:
            continue

    # 4. Registrar no histórico
    if descricao_lines:
        descricao = "Alterações realizadas:\n" + "\n".join(descricao_lines)
        LogAlteracao.objects.create(
            bem=bem,
            usuario=request.user,
            descricao=descricao
        )
    else:
        descricao = "Nenhuma alteração detectada"

    return Response({
        'success': True,
        'data': serializer.data,
        'log': descricao
    })

def format_field_values(field, old_value, new_value):
    """Formata valores para exibição amigável"""
    # Campos com choices
    if field.choices:
        choices_dict = dict(field.choices)
        return (
            choices_dict.get(old_value, str(old_value)),
            choices_dict.get(new_value, str(new_value))
        )
    
    # Campos de data/hora
    elif isinstance(field, models.DateTimeField):
        return (
            formats.date_format(old_value, "SHORT_DATETIME_FORMAT") if old_value else "Nenhum",
            formats.date_format(new_value, "SHORT_DATETIME_FORMAT") if new_value else "Nenhum"
        )
    
    # Campos de relacionamento
    elif isinstance(field, models.ForeignKey):
        return (
            str(old_value) if old_value else "Nenhum",
            str(new_value) if new_value else "Nenhum"
        )
    
    # Caso geral
    return (
        str(old_value) if old_value is not None else "Nenhum",
        str(new_value) if new_value is not None else "Nenhum"
    )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def excluir_bem(request, pk):
    """
    Exclui um bem com base no ID (pk) fornecido e registra a exclusão no log de alterações.
    """
    bem = get_object_or_404(Bem, pk=pk)

    # Salvar os dados do bem antes da exclusão
    nome_bem = bem.nome
    id_bem = bem.id

    # Criar log antes de deletar o bem
    LogAlteracao.objects.create(
        usuario=request.user,
        descricao=f"Bem excluído: {nome_bem} (ID: {id_bem})"
    )

    bem.delete()

    return Response({'success': True, 'message': 'Bem excluído com sucesso.'}, status=status.HTTP_204_NO_CONTENT)

from django.shortcuts import redirect, get_object_or_404
from rest_framework.decorators import api_view  
from .models import Bem, Categoria, Departamento, Fornecedor
from .serializers import BemSerializer


def editar_bem(request, pk):
    bem = get_object_or_404(Bem, pk=pk)
    
    if request.method == 'POST':        
        serializer = BemSerializer(bem, data=request.POST)
        if serializer.is_valid():
            serializer.save()
            return redirect('gerenciar_bens')  # ou outra rota de listagem/feedback
        else:
            context = {
                'bem': bem,
                'errors': serializer.errors,
                'categories': Categoria.objects.all(),
                'departments': Departamento.objects.all(),
                'suppliers': Fornecedor.objects.all(),
            }
            return render(request, 'core/editar_bem.html', context)
    
    else:        
        context = {
            'bem': bem,
            'categories': Categoria.objects.all(),
            'departments': Departamento.objects.all(),
            'suppliers': Fornecedor.objects.all(),
        }
        return render(request, 'core/editar_bem.html', context)
    
def simular_rfid(request):
    """
    Simula a leitura de uma tag RFID e cria uma movimentação para o Bem correspondente.
    É esperado que o parâmetro 'rfid' seja enviado na query string (GET).
    Opcionalmente, pode ser enviado 'destino' com o ID do Departamento de destino.
    """
    rfid_tag = request.GET.get('rfid')
    if not rfid_tag:
        return JsonResponse({'error': 'Parâmetro "rfid" não informado.'}, status=400)

    # Tenta buscar o Bem correspondente à tag RFID
    try:
        bem = Bem.objects.get(rfid_tag=rfid_tag)
    except Bem.DoesNotExist:
        return JsonResponse({'error': f'Nenhum bem encontrado para a tag {rfid_tag}.'}, status=404)

    # Verifica se foi informado um departamento de destino via GET
    destino_id = request.GET.get('destino')
    if destino_id:
        destino = get_object_or_404(Departamento, pk=destino_id)
    else:
        # Caso não seja informado, simula alternando para o primeiro departamento que não seja o atual
        destino = Departamento.objects.exclude(pk=bem.departamento.pk).first()
        if not destino:
            return JsonResponse({'error': 'Nenhum departamento alternativo disponível para movimentação.'}, status=400)

    # Cria a movimentação: a origem é o departamento atual do bem
    movimentacao = Movimentacao.objects.create(
        bem=bem,
        origem=bem.departamento,
        destino=destino,
        # O campo "responsavel" pode ser definido com o usuário logado ou None (simulação)
        responsavel=request.user if request.user.is_authenticated else None
    )

    # Atualiza o departamento do bem para o novo destino
    bem.departamento = destino
    bem.save()

    # Retorna uma resposta de sucesso
    resposta = {
        'mensagem': f"O bem '{bem.nome}' foi movido de '{movimentacao.origem}' para '{destino}'.",
        'bem_id': bem.id,
        'movimentacao_id': movimentacao.id,
        'data_movimentacao': movimentacao.data_movimentacao.strftime('%d/%m/%Y %H:%M')
    }
    return JsonResponse(resposta, status=200)

