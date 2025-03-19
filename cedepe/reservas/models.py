from django.db import models

class Quarto(models.Model):
    """ Representa um quarto que contém várias camas. """
    numero = models.CharField(max_length=10, unique=True)
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def camas_disponiveis(self):
        """ Retorna a quantidade de camas disponíveis no quarto. """
        return self.camas.filter(status='DISPONIVEL').count()

    def __str__(self):
        return f"Quarto {self.numero}"

class Cama(models.Model):
    """ Representa uma cama dentro de um quarto. """
    STATUS = (
        ('DISPONIVEL', 'Disponível'),
        ('OCUPADA', 'Ocupada'),
    )
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name="camas")
    identificacao = models.CharField(max_length=20)  # Exemplo: "Beliche Inferior", "Cama 1"
    status = models.CharField(max_length=10, choices=STATUS, default='DISPONIVEL')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.identificacao} - {self.quarto.numero} ({self.get_status_display()})"

class Hospede(models.Model):
    """ Representa um hóspede que ocupará uma cama. """
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    endereco = models.TextField()
    instituicao = models.CharField(max_length=150, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome


class Reserva(models.Model):
    """ Representa a reserva de uma cama por um hóspede. """
    STATUS = (
        ('ATIVA', 'Ativa'),
        ('CANCELADA', 'Cancelada'),
        ('FINALIZADA', 'Finalizada'),
    )
    hospede = models.ForeignKey(Hospede, on_delete=models.CASCADE)
    cama = models.ForeignKey(Cama, on_delete=models.CASCADE)
    data_checkin = models.DateField()
    data_checkout = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS, default='ATIVA')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """ Ao salvar uma reserva ativa, a cama fica ocupada. """
        if self.status == 'ATIVA':
            self.cama.status = 'OCUPADA'
        else:
            self.cama.status = 'DISPONIVEL'
        self.cama.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva {self.id} - {self.hospede.nome} ({self.cama})"
