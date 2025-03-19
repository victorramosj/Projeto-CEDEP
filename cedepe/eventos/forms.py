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

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('inicio')
        fim = cleaned_data.get('fim')
        sala = cleaned_data.get('sala')

        # Valida se o horário de início é anterior ao horário de fim
        if inicio and fim:
            if inicio >= fim:
                self.add_error('inicio', 'O horário de início deve ser anterior ao horário de fim.')
                self.add_error('fim', 'O horário de fim deve ser posterior ao horário de início.')
            if inicio < now():
                self.add_error('inicio', 'O horário de início não pode ser no passado.')

        # Valida conflitos de agendamento na mesma sala
        if sala and inicio and fim:
            conflitos = Agendamento.objects.filter(
                sala=sala,
                inicio__lt=fim,  # O início de outro evento deve ser menor que o fim do novo evento
                fim__gt=inicio   # O fim de outro evento deve ser maior que o início do novo evento
            )
            # Excluir o próprio agendamento em caso de atualização
            if self.instance.pk:
                conflitos = conflitos.exclude(pk=self.instance.pk)
            if conflitos.exists():
                self.add_error('sala', 'Já existe um agendamento nesse horário para essa sala.')

        return cleaned_data
