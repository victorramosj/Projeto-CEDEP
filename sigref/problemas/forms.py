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

# forms.py
from django import forms
from .models import AvisoImportante

from django import forms
from .models import AvisoImportante

from django import forms
from .models import AvisoImportante

class AvisoForm(forms.ModelForm):
    class Meta:
        model = AvisoImportante
        fields = ['titulo', 'mensagem', 'prioridade', 'data_expiracao', 'escola', 'setor_destino', 'ativo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'mensagem': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'data_expiracao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'escola': forms.Select(attrs={'class': 'form-select'}),
            'setor_destino': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].widget.attrs.update({'class': 'form-control'})
        self.fields['mensagem'].widget.attrs.update({'class': 'form-control'})
        self.fields['prioridade'].widget.attrs.update({'class': 'form-select'})
        self.fields['setor_destino'].widget.attrs.update({'class': 'form-select'})
        
    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if len(titulo) < 5:
            raise forms.ValidationError("O título precisa ter pelo menos 5 caracteres.")
        return titulo

from django import forms
from .models import AtualizacaoEscola

class AtualizacaoEscolaForm(forms.ModelForm):
    class Meta:
        model = AtualizacaoEscola
        fields = [
            'endereco', 'telefone', 'nome_gestor', 
            'telefone_gestor', 'email_escola', 'email_gestor', 'foto_fachada'
        ]
        widgets = {
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_gestor': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone_gestor': forms.TextInput(attrs={'class': 'form-control'}),
            'email_escola': forms.EmailInput(attrs={'class': 'form-control'}),
            'email_gestor': forms.EmailInput(attrs={'class': 'form-control'}),
            'foto_fachada': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }