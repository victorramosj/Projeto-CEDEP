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
from django.utils.timezone import now, make_aware
from rest_framework import serializers
from .models import Agendamento
from datetime import datetime

class AgendamentoSerializer(serializers.ModelSerializer):
    salas = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Sala.objects.all()
    )
    sala_nomes = serializers.SerializerMethodField()
    evento_titulo = serializers.CharField(source='evento.titulo', read_only=True)
    evento_descricao = serializers.CharField(source='evento.descricao', read_only=True)
    horario = serializers.SerializerMethodField()

    class Meta:
        model = Agendamento
        fields = '__all__'  # ou use: ['id', 'evento', 'salas', 'inicio', 'fim', 'participantes', ...]
    
    def get_sala_nomes(self, obj):
        return [sala.nome for sala in obj.salas.all()]
    
    def get_horario(self, obj):
        return f"{obj.inicio.strftime('%H:%M')} - {obj.fim.strftime('%H:%M')}"

    def validate(self, data):
        inicio = data.get('inicio')
        fim = data.get('fim')
        salas = data.get('salas')

        # Garantir timezone-aware
        if isinstance(inicio, datetime) and inicio.tzinfo is None:
            inicio = make_aware(inicio)
        if isinstance(fim, datetime) and fim.tzinfo is None:
            fim = make_aware(fim)

        if inicio and fim:
            if inicio >= fim:
                raise serializers.ValidationError({
                    "fim": "Horário de término deve ser posterior ao início."
                })
            if inicio < now():
                raise serializers.ValidationError({
                    "inicio": "Não é possível agendar no passado."
                })

        # Validação de conflito para cada sala
        if salas and inicio and fim:
            for sala in salas:
                conflitos = Agendamento.objects.filter(
                    salas=sala,
                    inicio__lt=fim,
                    fim__gt=inicio
                )
                if self.instance:
                    conflitos = conflitos.exclude(pk=self.instance.pk)
                if conflitos.exists():
                    raise serializers.ValidationError({
                        "salas": f"Conflito de horário na sala '{sala.nome}'."
                    })

        return data

