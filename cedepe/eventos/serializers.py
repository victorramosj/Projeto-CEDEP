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

from django.utils.timezone import now
from rest_framework import serializers
from .models import Agendamento

# serializers.py
class AgendamentoSerializer(serializers.ModelSerializer):
    sala_nome = serializers.CharField(source='sala.nome', read_only=True)
    evento_titulo = serializers.CharField(source='evento.titulo', read_only=True)
    evento_descricao = serializers.CharField(source='evento.descricao', read_only=True)
    horario = serializers.SerializerMethodField()
    class Meta:
        model = Agendamento
        fields = '__all__'
    def get_horario(self, obj):
        return f"{obj.inicio.strftime('%H:%M')} - {obj.fim.strftime('%H:%M')}"

    def validate(self, data):
        inicio = data.get('inicio')
        fim = data.get('fim')
        sala = data.get('sala')

        # Validação de horário
        if inicio and fim:
            if inicio >= fim:
                raise serializers.ValidationError({
                    "fim": "Horário de término deve ser posterior ao início."
                })
            if inicio < now():
                raise serializers.ValidationError({
                    "inicio": "Não é possível agendar no passado."
                })

        # Validação de conflito de horário na mesma sala
        qs = Agendamento.objects.filter(
            sala=sala,
            inicio__lt=fim,   # Início de outro evento é antes do fim do novo
            fim__gt=inicio    # Fim de outro evento é depois do início do novo
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({
                "sala": "Conflito de horário nesta sala."
            })

        return data

