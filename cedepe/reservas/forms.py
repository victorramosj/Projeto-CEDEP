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
        fields = ['nome', 'cpf', 'email', 'telefone', 'endereco']

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['hospede', 'cama', 'data_checkin', 'data_checkout', 'status']
