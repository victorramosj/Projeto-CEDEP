from rest_framework import serializers
from django.utils.timezone import now
from .models import Sala, Evento, Agendamento

class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = '__all__'

class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = '__all__'

class AgendamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agendamento
        fields = '__all__'

    def validate(self, data):
        """
        Valida se a sala já está ocupada no período selecionado e se o horário de fim é maior que o de início.
        """
        inicio = data.get('inicio')
        fim = data.get('fim')
        sala = data.get('sala')

        if inicio and fim and inicio >= fim:
            raise serializers.ValidationError({"horario": "O horário de início deve ser anterior ao horário de fim."})

        if inicio and inicio < now():
            raise serializers.ValidationError({"inicio": "O horário de início não pode ser no passado."})

        if sala and inicio and fim:
            conflitos = Agendamento.objects.filter(
                sala=sala,
                inicio__lt=fim,  # O início de outro evento deve ser menor que o fim do novo evento
                fim__gt=inicio  # O fim de outro evento deve ser maior que o início do novo evento
            )
            if conflitos.exists():
                raise serializers.ValidationError({"sala": "Já existe um agendamento nesse horário para essa sala."})

        return data
