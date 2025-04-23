from django import forms
from django.utils.timezone import now
from .models import Sala, Evento, Agendamento

class SalaForm(forms.ModelForm):
    class Meta:
        model = Sala
        fields = '__all__'

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = '__all__'

from django import forms
from django.utils.timezone import now
from .models import Agendamento

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = '__all__'
        widgets = {
            'evento': forms.Select(attrs={'class': 'form-select'}),
            # Alterando para SelectMultiple para permitir múltiplas salas:
            'salas': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'inicio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fim': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'participantes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('inicio')
        fim = cleaned_data.get('fim')
        salas = cleaned_data.get('salas')

        # Validação dos horários
        if inicio and fim:
            if inicio >= fim:
                self.add_error('fim', 'O horário de término deve ser posterior ao início.')
            if inicio < now():
                self.add_error('inicio', 'O horário de início não pode ser no passado.')

        # Validação de conflito em cada sala selecionada
        if salas and inicio and fim:
            for sala in salas:
                # Filtra agendamentos dessa sala com conflito de horário
                conflitos = Agendamento.objects.filter(
                    salas=sala,
                    inicio__lt=fim,
                    fim__gt=inicio
                )
                # Se estiver editando, exclua o próprio agendamento
                if self.instance and self.instance.pk:
                    conflitos = conflitos.exclude(pk=self.instance.pk)
                if conflitos.exists():
                    self.add_error('salas', f'Já existe um agendamento na sala {sala.nome} nesse horário.')

        return cleaned_data
