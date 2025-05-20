import os
import csv
import django
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sigref.settings")
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from monitoramento.models import (
    Setor, Escola, GREUser,
    Questionario, Pergunta, Monitoramento
)

TIPO_MAP = {
    'ADMINISTRADOR': 'ADMIN',
    'COORDENADOR': 'COORDENADOR',
    'CHEFE_DE_SETOR': 'CHEFE_SETOR',
    'MONITOR_ESCOLAR': 'MONITOR',
    'ESCOLA': 'ESCOLA',
    'CEDEPE': 'CEDEPE',
}

def limpar_tabelas():
    print("🧹 Limpando dados existentes…")
    Monitoramento.objects.all().delete()
    Pergunta.objects.all().delete()
    Questionario.objects.all().delete()
    GREUser.objects.exclude(user__is_superuser=True).delete()
    Setor.objects.all().delete()
    Escola.objects.all().delete()
    User.objects.exclude(is_superuser=True).delete()

def criar_superadmin():
    if not User.objects.filter(username='admin').exists():
        print("✨ Criando superusuário admin…")
        admin = User.objects.create_superuser(
            'admin', 'admin@sigref.local', 'ThunderC9#@!'
        )
        GREUser.objects.create(
            user=admin,
            tipo_usuario='ADMIN',
            nome_completo='Administrador Sistema'
        )
    else:
        print("✅ Superusuário admin já existe.")

def criar_setores():
    print("🌳 Criando setores…")
    estrutura = {
        "CGGR": [], "CGAF": ["UDP", "NAS", "NAE", "FINANCEIRO"],
        "CGIP": [], "CGDE": ["PSICOLOGIA", "UJC", "NEEI", "EDUCACAO"],
        "CGPA": [], "NOB": [], "CTI": [], "GABINETE": [],
    }
    setores = {}
    for nome, subs in estrutura.items():
        pai = Setor.objects.create(nome=nome)
        setores[nome] = pai
        for s in subs:
            setores[s] = Setor.objects.create(nome=s, parent=pai)
    print(f"→ {Setor.objects.count()} setores criados.")
    return setores

def importar_usuarios():
    path = os.path.join(settings.BASE_DIR, 'usuarios.csv')
    print(f"📥 Importando usuários de {path}…")
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            nome     = row['nome_completo'].strip()
            username = row['username'].strip()
            senha    = row['password'].strip()
            tipo_csv = row['tipo_usuario'].strip().upper()
            tipo     = TIPO_MAP.get(tipo_csv, 'MONITOR')

            user, user_created = User.objects.get_or_create(username=username)
            if user_created:
                user.set_password(senha)
                user.save()

            greuser, gre_created = GREUser.objects.get_or_create(
                user=user,
                defaults={
                    'nome_completo': nome,
                    'tipo_usuario': tipo
                }
            )

            if not gre_created:
                greuser.nome_completo = nome
                greuser.tipo_usuario = tipo
                greuser.save()

            print(f"• Usuário: {greuser.nome_completo} [{greuser.tipo_usuario}]")

import os
import csv
from django.conf import settings
from monitoramento.models import Escola, GREUser

def importar_escolas():
    path = os.path.join(settings.BASE_DIR, 'escolas.csv')
    print(f"📥 Importando escolas de {path}…")

    duplicados = []  # Armazena nomes com múltiplos usuários

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            nome   = row['nome'].strip()
            inep   = row['inep'].strip()

            escola, created = Escola.objects.update_or_create(
                inep=inep,
                defaults={
                    'nome':            nome,
                    'email_escola':    row['email_escola'].strip(),
                    'endereco':        row.get('endereco', '').strip(),
                    'foto_fachada':    row.get('foto_fachada', '').strip() or None,
                    'nome_gestor':     row['nome_gestor'].strip(),
                    'telefone_gestor': row['telefone_gestor'].strip(),
                    'email_gestor':    row['email_gestor'].strip(),
                }
            )

            try:
                gre = GREUser.objects.get(nome_completo__iexact=nome)
                escola.user = gre.user
                escola.save()
                gre.escolas.add(escola)
                print(f"→ Associada '{escola.nome}' ao usuário '{gre.user.username}'")
            except GREUser.DoesNotExist:
                print(f"⚠️ Nenhum usuário encontrado com nome: {nome}")
            except GREUser.MultipleObjectsReturned:
                print(f"⚠️ Múltiplos usuários encontrados com nome: {nome}")
                duplicados.append(nome)

            print(f"• Escola: {escola.nome} (INEP {escola.inep})")

    # Exibe duplicatas no final
    if duplicados:
        print("\n❗ Usuários com nomes duplicados encontrados:")
        for nome in set(duplicados):
            print(f" - {nome}")
    else:
        print("\n✅ Nenhuma duplicata de usuário encontrada.")


def criar_questionarios_exemplo(setores):
    print("📝 Criando questionários de exemplo…")
    admin_user = GREUser.objects.filter(tipo_usuario='ADMIN').first().user
    escolas = list(Escola.objects.all())
    if not escolas:
        print("⚠️ Sem escolas cadastradas: não foram criados questionários.")
        return []

    qs = []
    for nome, setor in setores.items():
        q = Questionario.objects.create(
            titulo=f"Questionário {nome}",
            descricao=f"Avaliação do setor {nome}",
            setor=setor,
            criado_por=admin_user
        )
        for e in random.sample(escolas, min(5, len(escolas))):
            q.escolas_destino.add(e)
        for ordem in range(1, 4):
            Pergunta.objects.create(
                questionario=q,
                ordem=ordem,
                texto=f"Pergunta {ordem} sobre {nome}?",
                tipo_resposta=random.choice(['SN', 'NU', 'TX'])
            )
        qs.append(q)
        print(f"• Questionário criado: {q.titulo}")
    return qs

def criar_monitoramentos_exemplo(qs):
    print("📊 Criando monitoramentos de exemplo…")
    candidatos = GREUser.objects.filter(tipo_usuario__in=['MONITOR', 'ESCOLA'])
    if not candidatos.exists():
        print("⚠️ Sem usuários MONITOR/ESCOLA: não foram criados monitoramentos.")
        return

    count = 0
    for q in qs:
        for e in q.escolas_destino.all():
            gre = random.choice(candidatos)
            Monitoramento.objects.create(
                questionario=q,
                escola=e,
                respondido_por=gre.user
            )
            count += 1
    print(f"→ {count} monitoramentos criados.")

def main():
    limpar_tabelas()
    criar_superadmin()
    setores = criar_setores()
    importar_usuarios()
    importar_escolas()
    qs = criar_questionarios_exemplo(setores)
    criar_monitoramentos_exemplo(qs)
    print("🎉 População completa executada com sucesso!")

if __name__ == "__main__":
    main()
