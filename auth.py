import hashlib
import hmac
import secrets
import sqlite3

from database import conectar, registrar_log
from common import ITERACOES, TAM_SENHA
from estrutura_v110 import consultar_vinculos
from permissoes import PERFIS, exigir_permissao_usuario


def gerar_hash(senha):
    if len(senha) < TAM_SENHA:
        raise ValueError(f"A senha deve ter pelo menos {TAM_SENHA} caracteres.")

    salt = secrets.token_bytes(16)
    derivado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES)

    return f"pbkdf2_sha256${ITERACOES}${salt.hex()}${derivado.hex()}"


def verificar_senha(senha, hash_armazenado):
    try:
        algoritmo, iteracoes, salt_hex, hash_hex = hash_armazenado.split("$")

        if algoritmo != "pbkdf2_sha256":
            return False

        derivado = hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), int(iteracoes)
        )

        return hmac.compare_digest(derivado, bytes.fromhex(hash_hex))
    except (ValueError, TypeError):
        return False


def autenticar(login, senha):
    login = login.strip()

    with conectar() as conexao:
        usuario = conexao.execute(
            """
            SELECT id, nome, login, senha_hash, perfil
            FROM usuarios
            WHERE login = ? AND ativo = 1
            """,
            (login,),
        ).fetchone()

        # Usuário inexistente ou inativo.
        if usuario is None:
            registrar_log(
                conexao,
                acao="login",
                usuario_login=login,
                resultado="falha",
                detalhes={"motivo": "credenciais_invalidas"},
            )
            return None

        # Senha incorreta.
        if not verificar_senha(senha, usuario["senha_hash"]):
            registrar_log(
                conexao,
                acao="login",
                usuario_id=usuario["id"],
                usuario_login=usuario["login"],
                resultado="falha",
                detalhes={"motivo": "credenciais_invalidas"},
            )
            return None

        # Autenticação bem-sucedida.
        registrar_log(
            conexao,
            acao="login",
            usuario_id=usuario["id"],
            usuario_login=usuario["login"],
            resultado="sucesso",
        )

        return {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "login": usuario["login"],
            "perfil": usuario["perfil"],
        }


def criar_usuario(nome, login, senha, perfil, ator_id=None, ator_login=None):
    """
    Cadastra um usuário.

    - Instalação inicial: permite criar o primeiro admin.
    - Sistema em uso: exige um superadministrador ativo.
    - Registra a operação na auditoria.
    """

    if perfil not in PERFIS:
        raise ValueError("Perfil inválido.")

    nome = nome.strip()
    login = login.strip()

    if not nome or not login:
        raise ValueError("Nome e login são obrigatórios.")

    senha_hash = gerar_hash(senha)

    with conectar() as conexao:
        # Protege a verificação e a inclusão na mesma transação.
        conexao.execute("BEGIN IMMEDIATE")

        total_usuarios = conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

        if total_usuarios == 0:
            # Compatibilidade com criar_admin.py.
            # A primeira conta é criada pelo procedimento de
            # instalação, antes da configuração do superadmin.
            if ator_id is not None or perfil != "admin":
                raise PermissionError(
                    "A primeira conta deve ser um administrador inicial."
                )

            login_responsavel = "sistema"

        else:
            # Nunca confia apenas no perfil da sessão.
            exigir_permissao_usuario(
                conexao,
                ator_id,
                "gerenciar_usuarios",
            )

            ator = conexao.execute(
                "SELECT login FROM usuarios WHERE id = ?",
                (ator_id,),
            ).fetchone()

            login_responsavel = ator["login"]

        cursor = conexao.execute(
            """
            INSERT INTO usuarios (
                nome, login, senha_hash, perfil
            )
            VALUES (?, ?, ?, ?)
            """,
            (nome, login, senha_hash, perfil),
        )

        novo_id = cursor.lastrowid

        registrar_log(
            conexao,
            acao="criar_usuario",
            usuario_id=ator_id,
            usuario_login=login_responsavel,
            entidade="usuarios",
            entidade_id=novo_id,
            detalhes={
                "login_criado": login,
                "perfil": perfil,
            },
        )

        return novo_id


def listar_usuarios(ator_id):
    """
    Lista as contas cadastradas no PrestServ.

    Somente superadministradores ativos podem consultar
    a relação de usuários.

    Não retorna senhas nem hashes de senhas.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "gerenciar_usuarios",
        )

        registros = conexao.execute("""
            SELECT
                id,
                nome,
                login,
                perfil,
                ativo,
                criado_em
            FROM usuarios
            ORDER BY nome COLLATE NOCASE, id
            """).fetchall()

    return [dict(registro) for registro in registros]


def redefinir_senha(usuario_id, nova_senha, ator_id):
    """
    Redefine a senha de um usuário.

    Somente superadministradores ativos podem
    executar esta operação.
    """

    senha_hash = gerar_hash(nova_senha)

    with conectar() as conexao:
        # Garante que a autorização e a alteração
        # aconteçam dentro da mesma transação.
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(
            conexao,
            ator_id,
            "gerenciar_usuarios",
        )

        ator = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        cursor = conexao.execute(
            """
            UPDATE usuarios
            SET senha_hash = ?
            WHERE id = ?
            """,
            (senha_hash, usuario_id),
        )

        if cursor.rowcount == 0:
            raise ValueError("Usuário não encontrado.")

        # Nunca armazena senhas ou hashes nos logs.
        registrar_log(
            conexao,
            acao="redefinir_senha_usuario",
            usuario_id=ator_id,
            usuario_login=ator["login"],
            entidade="usuarios",
            entidade_id=usuario_id,
        )


def atualizar_usuario(usuario_id, nome, login, perfil, ator_id):
    """
    Atualiza os dados e o papel de um usuário.

    Somente superadministradores ativos podem executar
    esta operação.

    Protege a própria conta e o último superadmin ativo.
    """

    nome = nome.strip()
    login = login.strip()

    if not nome:
        raise ValueError("O nome é obrigatório.")

    if not login:
        raise ValueError("O login é obrigatório.")

    if perfil not in PERFIS:
        raise ValueError("Perfil inválido.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        # Verifica a autorização diretamente no banco.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "gerenciar_usuarios",
        )

        ator = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        usuario = conexao.execute(
            """
            SELECT id, nome, login, perfil, ativo
            FROM usuarios
            WHERE id = ?
            """,
            (usuario_id,),
        ).fetchone()

        if usuario is None:
            raise ValueError("Usuário não encontrado.")

        # Impede que o superadmin retire seus
        # próprios privilégios.
        if usuario_id == ator_id and perfil != "superadmin":
            raise ValueError(
                "Você não pode remover seu próprio " "perfil de superadministrador."
            )

        # Protege o último superadministrador ativo.
        if (
            usuario["perfil"] == "superadmin"
            and usuario["ativo"]
            and perfil != "superadmin"
        ):
            total = conexao.execute("""
                SELECT COUNT(*)
                FROM usuarios
                WHERE perfil = 'superadmin'
                  AND ativo = 1
                """).fetchone()[0]

            if total <= 1:
                raise ValueError(
                    "O último superadministrador ativo " "não pode ser rebaixado."
                )

        novos_dados = {
            "nome": nome,
            "login": login,
            "perfil": perfil,
        }

        alteracoes = {}

        for campo, novo_valor in novos_dados.items():
            valor_anterior = usuario[campo]

            if valor_anterior != novo_valor:
                alteracoes[campo] = {
                    "antes": valor_anterior,
                    "depois": novo_valor,
                }

        # Não grava nem registra log se nada mudou.
        if not alteracoes:
            return

        conexao.execute(
            """
            UPDATE usuarios
            SET nome = ?,
                login = ?,
                perfil = ?
            WHERE id = ?
            """,
            (nome, login, perfil, usuario_id),
        )

        registrar_log(
            conexao,
            acao="atualizar_usuario",
            usuario_id=ator_id,
            usuario_login=ator["login"],
            entidade="usuarios",
            entidade_id=usuario_id,
            detalhes={"alteracoes": alteracoes},
        )


def definir_status_usuario(usuario_id, ativo, ator_id):
    """
    Ativa ou desativa uma conta de usuário.

    Somente superadministradores ativos podem executar
    esta operação.

    Impede a autodesativação e protege o último
    superadministrador ativo.
    """

    novo_status = int(bool(ativo))

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        # Valida o operador diretamente no banco.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "gerenciar_usuarios",
        )

        ator = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        usuario = conexao.execute(
            """
            SELECT id, perfil, ativo
            FROM usuarios
            WHERE id = ?
            """,
            (usuario_id,),
        ).fetchone()

        if usuario is None:
            raise ValueError("Usuário não encontrado.")

        # Impede desativar a própria conta.
        if usuario_id == ator_id and not novo_status:
            raise ValueError("Você não pode desativar sua própria conta.")

        # Protege o último superadministrador ativo.
        if usuario["perfil"] == "superadmin" and usuario["ativo"] and not novo_status:
            total = conexao.execute("""
                SELECT COUNT(*)
                FROM usuarios
                WHERE perfil = 'superadmin'
                  AND ativo = 1
                """).fetchone()[0]

            if total <= 1:
                raise ValueError(
                    "O último superadministrador ativo " "não pode ser desativado."
                )

        # Nenhuma alteração necessária.
        if usuario["ativo"] == novo_status:
            return

        conexao.execute(
            """
            UPDATE usuarios
            SET ativo = ?
            WHERE id = ?
            """,
            (novo_status, usuario_id),
        )

        # Auditoria na mesma transação.
        registrar_log(
            conexao,
            acao=("ativar_usuario" if novo_status else "desativar_usuario"),
            usuario_id=ator_id,
            usuario_login=ator["login"],
            entidade="usuarios",
            entidade_id=usuario_id,
            detalhes={
                "ativo_anterior": bool(usuario["ativo"]),
                "ativo_novo": bool(novo_status),
            },
        )


def excluir_usuario(usuario_id, ator_id):
    """
    Exclui um usuário somente quando autorizado.

    Somente superadministradores ativos podem excluir.
    Preserva a proteção contra relacionamentos e registra
    a exclusão na auditoria.
    """

    if type(usuario_id) is not int or usuario_id <= 0:
        raise ValueError("Identificador do usuário inválido.")

    with conectar() as conexao:
        # Evita alterações concorrentes entre a verificação
        # das regras e a exclusão.
        conexao.execute("BEGIN IMMEDIATE")

        # Autoriza somente superadministradores ativos.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "gerenciar_usuarios",
        )

        ator = conexao.execute(
            """
            SELECT id, login
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

        # Impede a exclusão da própria conta.
        if usuario_id == ator_id:
            raise ValueError("Você não pode excluir sua própria conta.")

        usuario = conexao.execute(
            """
            SELECT id, login, perfil, ativo
            FROM usuarios
            WHERE id = ?
            """,
            (usuario_id,),
        ).fetchone()

        if usuario is None:
            raise ValueError("Usuário não encontrado.")

        # Protege o último superadministrador ativo.
        if usuario["perfil"] == "superadmin" and usuario["ativo"]:
            total = conexao.execute("""
                SELECT COUNT(*)
                FROM usuarios
                WHERE perfil = 'superadmin'
                  AND ativo = 1
                """).fetchone()[0]

            if total <= 1:
                raise ValueError(
                    "O último superadministrador ativo " "não pode ser excluído."
                )

        # Preserva a proteção da V1.1 contra exclusões
        # de usuários com relacionamentos operacionais.
        vinculos = consultar_vinculos(
            conexao,
            "usuarios",
            usuario_id,
        )

        if vinculos:
            raise ValueError(
                "Este usuário possui relacionamentos com "
                "outras tabelas. Utilize a desativação."
            )

        try:
            cursor = conexao.execute(
                "DELETE FROM usuarios WHERE id = ?",
                (usuario_id,),
            )

        except sqlite3.IntegrityError as erro:
            raise ValueError(
                "Exclusão bloqueada por relacionamento no banco."
            ) from erro

        if cursor.rowcount != 1:
            raise RuntimeError("A exclusão não foi concluída.")

        # Preserva a auditoria, na mesma transação.
        registrar_log(
            conexao,
            acao="excluir_usuario",
            usuario_id=ator["id"],
            usuario_login=ator["login"],
            entidade="usuarios",
            entidade_id=usuario_id,
            detalhes={
                "login_excluido": usuario["login"],
                "perfil_excluido": usuario["perfil"],
            },
        )
