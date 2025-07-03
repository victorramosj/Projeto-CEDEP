from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import LoginForm

from django.shortcuts import render, redirect
from monitoramento.models import GREUser


from django.shortcuts import redirect, render
from monitoramento.models import GREUser
from problemas.models import Lacuna, ProblemaUsuario

def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, "cedepe/home.html")

    try:
        # Obtendo o usuário logado
        gre_user = request.user.greuser
        
        # Obter o setor do usuário (se for um "Chefe de Setor" ou "Coordenador")
        setor_do_usuario = gre_user.setor
        escolas = gre_user.escolas.all()  # Obtendo as escolas do usuário, caso ele tenha várias

        # Filtrar lacunas para as escolas do usuário
        lacunas_pendentes = Lacuna.objects.filter(escola__in=escolas, status='P')

        # Filtrar problemas para o setor do usuário
        problemas_pendentes = ProblemaUsuario.objects.filter(setor=setor_do_usuario, status='P')

        # Criar alertas para lacunas e problemas pendentes
        alerts = []

        # Se houver lacunas pendentes
        if lacunas_pendentes.exists():
            alerts.append({
                'type': 'lacuna',
                'count': lacunas_pendentes.count(),
                'url': 'tela_lacunas',  # URL para a tela de lacunas
                'text': f"Você tem {lacunas_pendentes.count()} lacuna(s) pendente(s)."
            })

        # Se houver problemas pendentes
        if problemas_pendentes.exists():
            alerts.append({
                'type': 'problema',
                'count': problemas_pendentes.count(),
                'url': 'tela_problemas',  # URL para a tela de problemas
                'text': f"Você tem {problemas_pendentes.count()} problema(s) pendente(s)."
            })

        # Verificar se o usuário é da escola e redirecionar para o dashboard da escola
        if gre_user.is_escola():
            return redirect('escola_dashboard')

        # Para qualquer outro tipo de usuário, renderizar a página principal com os alertas
        return render(request, "cedepe/home.html", {"alerts": alerts})

    except GREUser.DoesNotExist:
        return render(request, "cedepe/home.html")





from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import LoginForm  # Certifique-se de importar corretamente
from monitoramento.models import GREUser  # Importa o modelo de usuário extendido

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)

                try:
                    gre_user = GREUser.objects.get(user=user)

                    # Exemplo: armazenar tipo de usuário na sessão
                    request.session['tipo_usuario'] = gre_user.tipo_usuario
                    request.session['nome_completo'] = gre_user.nome_completo
                    request.session['nivel_acesso'] = gre_user.nivel_acesso

                    messages.success(request, f"Bem-vindo, {gre_user.nome_completo}!")

                    # Redirecionamento inteligente (ajuste conforme sua lógica)
                    if gre_user.is_admin():
                        return redirect('home')
                    elif gre_user.is_coordenador():
                        return redirect('home')
                    elif gre_user.is_chefe_setor():
                        return redirect('home')
                    elif gre_user.is_monitor():
                        return redirect('home')
                    elif gre_user.is_escola():
                        return redirect('escola_dashboard')
                    else:
                        return redirect('home')  # fallback padrão

                except GREUser.DoesNotExist:
                    # Se o usuário estiver autenticado, mas não tiver um GREUser associado
                    messages.warning(request, "Usuário autenticado, mas sem perfil configurado.")
                    return redirect("home")
            else:
                messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = LoginForm()
    
    return render(request, "cedepe/login.html", {"form": form})


def user_logout(request):
    logout(request)
    messages.info(request, "Você saiu da conta.")
    return redirect("home")

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "cedepe/register.html", {"form": form})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .forms import LoginForm
from monitoramento.models import GREUser, Escola, Setor # Importe Escola e Setor também
from problemas.models import Lacuna, ProblemaUsuario # Para o dashboard, se necessário
from rest_framework.authtoken.models import Token # Importe o modelo Token


@csrf_exempt
def api_login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'success': False, 'message': 'Usuário e senha são obrigatórios.'}, status=400)

            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Autenticação bem-sucedida, agora busca os detalhes do GREUser
                try:
                    gre_user = GREUser.objects.get(user=user)
                    
                    # Gera ou recupera o token de autenticação para o usuário
                    token, created = Token.objects.get_or_create(user=user)

                    user_data = {
                        'success': True,
                        'token': token.key, # Retorna o token de autenticação
                        'full_name': gre_user.nome_completo,
                        'user_type': gre_user.tipo_usuario,
                        'user_type_display': gre_user.get_tipo_usuario_display(),
                        'access_level': gre_user.nivel_acesso,
                        'email': user.email,
                        'username': user.username,
                        'celular': gre_user.celular,
                        'cpf': gre_user.cpf,
                    }

                    if gre_user.is_escola() or gre_user.is_monitor():
                        user_data['escolas'] = list(gre_user.escolas.values('id', 'nome', 'inep', 'email_escola', 'nome_gestor'))
                    
                    if gre_user.setor:
                        user_data['setor'] = {
                            'id': gre_user.setor.id,
                            'nome': gre_user.setor.nome,
                            'hierarquia_completa': gre_user.setor.hierarquia_completa,
                        }
                    
                    return JsonResponse(user_data)

                except GREUser.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Perfil de usuário não configurado. Contate o administrador.'}, status=403)
            else:
                return JsonResponse({'success': False, 'message': 'Usuário ou senha inválidos.'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Requisição JSON inválida.'}, status=400)
        except Exception as e:
            print(f"Erro na api_login: {e}")
            return JsonResponse({'success': False, 'message': f'Um erro inesperado ocorreu: {str(e)}'}, status=500)
    else:
        return JsonResponse({'success': False, 'message': 'Método não permitido.'}, status=405)