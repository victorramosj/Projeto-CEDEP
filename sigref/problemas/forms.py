from django import forms
from .models import ProblemaUsuario, Lacuna
from monitoramento.models import Setor  # <- Corrigido aqui

class ProblemaUsuarioForm(forms.ModelForm):
    class Meta:
        model = ProblemaUsuario
        fields = ['setor', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descreva o problema...',
                'rows': 4
            }),
            'setor': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'descricao': 'Problema',
            'setor': 'Setor',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['setor'].queryset = Setor.objects.all()

class LacunaForm(forms.ModelForm):
    class Meta:
        model = Lacuna
        fields = ['disciplina', 'carga_horaria']
        widgets = {
            'disciplina': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da disciplina'
            }),
            'carga_horaria': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Carga horária (em horas-aula)',
                'min': 1
            }),
        }
        labels = {
            'disciplina': 'Disciplina',
            'carga_horaria': 'Carga Horária',
        }

from django import forms
from .models import ProblemaUsuario, Lacuna, AvisoImportante
from monitoramento.models import Setor

class ProblemaUsuarioForm(forms.ModelForm):
    class Meta:
        model = ProblemaUsuario
        fields = ['setor', 'descricao','anexo']
        widgets = {
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descreva o problema...',
                'rows': 4
            }),
            'setor': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'descricao': 'Problema',
            'setor': 'Setor',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['setor'].queryset = Setor.objects.all()

class LacunaForm(forms.ModelForm):
    class Meta:
        model = Lacuna
        fields = ['disciplina', 'carga_horaria']
        widgets = {
            'disciplina': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da disciplina'
            }),
            'carga_horaria': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Carga horária (em horas-aula)',
                'min': 1
            }),
        }
        labels = {
            'disciplina': 'Disciplina',
            'carga_horaria': 'Carga Horária',
        }

# Em seu arquivo forms.py
from django import forms
from django.utils import timezone # <-- Importe o timezone
from .models import AvisoImportante

class AvisoForm(forms.ModelForm):
    class Meta:
        model = AvisoImportante
        
        # --- CORREÇÃO 1: CAMPOS ---
        # Listamos APENAS os campos que o usuário realmente edita no modal.
        # Isso impede que campos como 'ativo' e 'escola' sejam apagados acidentalmente.
        fields = [
            'titulo',
            'mensagem',
            'prioridade',
            'data_expiracao',
        ]

        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'mensagem': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'data_expiracao': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    # --- CORREÇÃO 2: FUSO HORÁRIO ---
    # Adicionamos este método para tratar a data de expiração.
    def clean_data_expiracao(self):
        # Pega a data já validada pelo Django
        data = self.cleaned_data.get('data_expiracao')
        
        # Se a data existir e for "ingênua" (sem fuso horário)...
        if data and timezone.is_naive(data):
            # ...a tornamos "consciente", usando o fuso horário padrão do seu projeto (definido em settings.py)
            return timezone.make_aware(data)
            
        # Retorna a data (seja ela já consciente ou nula)
        return data

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if len(titulo) < 5:
            raise forms.ValidationError("O título precisa ter pelo menos 5 caracteres.")
        return titulo