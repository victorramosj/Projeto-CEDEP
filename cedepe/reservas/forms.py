# reservas/forms.py
from django import forms
from .models import Quarto, Cama, Hospede, Reserva

class QuartoForm(forms.ModelForm):
    class Meta:
        model = Quarto
        fields = ['numero', 'descricao']

class CamaForm(forms.ModelForm):
    class Meta:
        model = Cama
        fields = ['quarto', 'identificacao', 'status']

class HospedeForm(forms.ModelForm):
    class Meta:
        model = Hospede
        fields = ['nome', 'cpf', 'email', 'telefone', 'instituicao', 'endereco']

from django import forms
from django.utils import timezone  # Importação do timezone
from django.core.exceptions import ValidationError
from .models import Reserva, Cama, Hospede

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['hospede', 'cama', 'data_checkin', 'data_checkout', 'status']
        widgets = {
            'data_checkin': forms.DateInput(attrs={'type': 'date'}),
            'data_checkout': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        cama = cleaned_data.get('cama')
        hospede = cleaned_data.get('hospede')
        data_checkin = cleaned_data.get('data_checkin')
        data_checkout = cleaned_data.get('data_checkout')
        status = cleaned_data.get('status')

        # Data atual com fuso horário correto
        hoje = timezone.now().date()

        if cama and cama.status != 'DISPONIVEL':
            raise ValidationError("A cama selecionada não está disponível para reserva.")

        if hospede and Reserva.objects.filter(hospede=hospede, status='ATIVA').exists():
            raise ValidationError("Este hóspede já possui uma reserva ativa.")

        if data_checkin and data_checkout and data_checkin >= data_checkout:
            raise ValidationError("A data de check-in deve ser anterior à data de check-out.")

        # Verificação com fuso horário correto
        if data_checkin and data_checkin < hoje:
            raise ValidationError("A data de check-in não pode ser no passado.")

        return cleaned_data

    def save(self, commit=True):
        reserva = super().save(commit=False)
        hoje = timezone.now().date()  # Data atual com fuso correto

        if reserva.status == 'ATIVA':
            reserva.cama.status = 'OCUPADA'
        elif reserva.status in ['CANCELADA', 'FINALIZADA']:
            reserva.cama.status = 'DISPONIVEL'
            # Se finalizada, atualiza data_checkout para hoje
            if reserva.status == 'FINALIZADA':
                reserva.data_checkout = hoje

        if commit:
            reserva.cama.save()
            reserva.save()

        return reserva