from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import LoginForm

def dashboard(request):
    return render(request, 'gestao_patrimonio/home.html')

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)  # Usa LoginForm
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bem-vindo, {username}!")
                return redirect("home")
        messages.error(request, "Usuário ou senha inválidos")
    else:
        form = LoginForm()  # Usa LoginForm
    return render(request, "gestao_patrimonio/login.html", {"form": form})

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
    return render(request, "gestao_patrimonio/register.html", {"form": form})
