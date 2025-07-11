import os
import csv
import django
import random
import re
import unicodedata
from django.db.models import Q

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

def normalizar_texto(texto):
    """Normaliza texto para comparação: remove acentos, espaços e converte para maiúsculas"""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = re.sub(r'\W+', '', texto).upper()
    return texto

def associar_setor_por_username(greuser, setores):
    """Associa setor baseado na similaridade do nome de usuário com o nome do setor"""
    username_norm = normalizar_texto(greuser.user.username)
    
    # Tentar encontrar correspondência exata primeiro
    for setor_nome, setor_obj in setores.items():
        setor_nome_norm = normalizar_texto(setor_nome)
        if setor_nome_norm == username_norm:
            greuser.setor = setor_obj
            greuser.save()
            print(f"→ Associado setor '{setor_nome}' ao usuário '{greuser.user.username}'")
            return True
    
    # Tentar correspondência parcial
    for setor_nome, setor_obj in setores.items():
        setor_nome_norm = normalizar_texto(setor_nome)
        if setor_nome_norm in username_norm or username_norm in setor_nome_norm:
            greuser.setor = setor_obj
            greuser.save()
            print(f"→ Associado setor '{setor_nome}' ao usuário '{greuser.user.username}' (correspondência parcial)")
            return True
    
    return False

def importar_usuarios(setores):
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

            # Marcar como staff se não for escola
            if tipo != 'ESCOLA':
                user.is_staff = True
            else:
                user.is_staff = False  # opcional, para garantir

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

            # Tentar associar setor automaticamente
            associar_setor_por_username(greuser, setores)
            
            print(f"• Usuário: {greuser.nome_completo} [{greuser.tipo_usuario}]")


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
                # Busca por nome completo ou username
                gre = GREUser.objects.get(
                    Q(nome_completo__iexact=nome) | 
                    Q(user__username__iexact=nome)
                )

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

def associar_escolas_usuarios_nao_escola():
    """Associa todas as escolas a todos os usuários que não são escolas"""
    print("🏫 Associando escolas a usuários não-escolares...")
    usuarios_nao_escola = GREUser.objects.exclude(tipo_usuario='ESCOLA')
    todas_escolas = Escola.objects.all()
    
    count = 0
    for usuario in usuarios_nao_escola:
        # Adiciona todas as escolas, evitando duplicatas
        escolas_atuais = usuario.escolas.all()
        novas_escolas = [e for e in todas_escolas if e not in escolas_atuais]
        
        if novas_escolas:
            usuario.escolas.add(*novas_escolas)
            count += len(novas_escolas)
            print(f"→ Associadas {len(novas_escolas)} escolas ao usuário {usuario}")
    
    print(f"✅ Total de {count} associações escola-usuário criadas.")

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
    importar_usuarios(setores)  # Passa setores para associação
    importar_escolas()
    associar_escolas_usuarios_nao_escola()  # Nova função
    qs = criar_questionarios_exemplo(setores)
    criar_monitoramentos_exemplo(qs)
    print("🎉 População completa executada com sucesso!")

if __name__ == "__main__":
    main()