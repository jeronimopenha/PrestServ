import hashlib
import hmac
import secrets
import sqlite3

from database import conectar, registrar_log
from common import ITERACOES, TAM_SENHA
from estrutura_v110 import consultar_vinculos


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
    if perfil not in ("admin", "porteiro"):
        raise ValueError("Perfil inválido.")

    nome = nome.strip()
    login = login.strip()

    if not nome or not login:
        raise ValueError("Nome e login são obrigatórios.")

    senha_hash = gerar_hash(senha)

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO usuarios (nome, login, senha_hash, perfil)
            VALUES (?, ?, ?, ?)
            """,
            (nome, login, senha_hash, perfil),
        )

        novo_id = cursor.lastrowid

        registrar_log(
            conexao,
            acao="criar_usuario",
            usuario_id=ator_id,
            usuario_login=ator_login or "sistema",
            entidade="usuarios",
            entidade_id=novo_id,
            detalhes={
                "login_criado": login,
                "perfil": perfil,
            },
        )

        return novo_id


def listar_usuarios():
    with conectar() as conexao:
        registros = conexao.execute("""
            SELECT id, nome, login, perfil, ativo, criado_em
            FROM usuarios
            ORDER BY nome
            """).fetchall()

    return [dict(registro) for registro in registros]


def alterar_status_usuario(usuario_id, ativo):
    with conectar() as conexao:
        conexao.execute(
            "UPDATE usuarios SET ativo = ? WHERE id = ?", (int(ativo), usuario_id)
        )


def redefinir_senha(usuario_id, nova_senha, ator_id):
    senha_hash = gerar_hash(nova_senha)

    with conectar() as conexao:
        # Identifica e valida o administrador responsável.
        ator = conexao.execute(
            """
            SELECT login, perfil, ativo
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

        if ator is None or ator["perfil"] != "admin" or not ator["ativo"]:
            raise ValueError("Administrador responsável inválido.")

        # Atualiza a senha.
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

        # Registra a operação, sem armazenar senhas.
        registrar_log(
            conexao,
            acao="redefinir_senha_usuario",
            usuario_id=ator_id,
            usuario_login=ator["login"],
            entidade="usuarios",
            entidade_id=usuario_id,
        )


def atualizar_usuario(usuario_id, nome, login, perfil, ator_id):
    nome = nome.strip()
    login = login.strip()

    if not nome:
        raise ValueError("O nome é obrigatório.")

    if not login:
        raise ValueError("O login é obrigatório.")

    if perfil not in ("admin", "porteiro"):
        raise ValueError("Perfil inválido.")

    with conectar() as conexao:
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

        if usuario_id == ator_id and perfil != "admin":
            raise ValueError(
                "Você não pode remover seu próprio perfil de administrador."
            )

        if usuario["perfil"] == "admin" and usuario["ativo"] and perfil != "admin":
            total = conexao.execute("""
                SELECT COUNT(*)
                FROM usuarios
                WHERE perfil = 'admin' AND ativo = 1
                """).fetchone()[0]

            if total <= 1:
                raise ValueError("O último administrador ativo não pode ser rebaixado.")

        ator = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        if ator is None:
            raise ValueError("Administrador responsável não encontrado.")

        conexao.execute(
            """
            UPDATE usuarios
            SET nome = ?, login = ?, perfil = ?
            WHERE id = ?
            """,
            (nome, login, perfil, usuario_id),
        )

        alteracoes = {}

        novos_dados = {
            "nome": nome,
            "login": login,
            "perfil": perfil,
        }

        for campo, novo_valor in novos_dados.items():
            valor_anterior = usuario[campo]

            if valor_anterior != novo_valor:
                alteracoes[campo] = {
                    "antes": valor_anterior,
                    "depois": novo_valor,
                }

        if alteracoes:
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
    if usuario_id == ator_id and not ativo:
        raise ValueError("Você não pode desativar sua própria conta.")

    with conectar() as conexao:
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

        if usuario["perfil"] == "admin" and usuario["ativo"] and not ativo:
            total = conexao.execute("""
                SELECT COUNT(*)
                FROM usuarios
                WHERE perfil = 'admin' AND ativo = 1
                """).fetchone()[0]

            if total <= 1:
                raise ValueError(
                    "O último administrador ativo não pode ser desativado."
                )

        novo_status = int(bool(ativo))

        # Não registra alterações quando o status continua igual.
        if usuario["ativo"] == novo_status:
            return

        # Identifica o administrador responsável.
        ator = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        if ator is None:
            raise ValueError("Administrador responsável não encontrado.")

        # Atualiza o status.
        conexao.execute(
            """
            UPDATE usuarios
            SET ativo = ?
            WHERE id = ?
            """,
            (novo_status, usuario_id),
        )

        # Registra a operação na mesma transação.
        registrar_log(
            conexao,
            acao="ativar_usuario" if novo_status else "desativar_usuario",
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
    """Exclui um usuário somente quando a operação é permitida."""

    if type(usuario_id) is not int or usuario_id <= 0:
        raise ValueError("Identificador do usuário inválido.")

    with conectar() as conexao:
        # Impede alterações concorrentes durante a verificação.
        conexao.execute("BEGIN IMMEDIATE")

        # Verifica se o responsável é um administrador ativo.
        ator = conexao.execute(
            """
            SELECT id, login
            FROM usuarios
            WHERE id = ?
              AND perfil = 'admin'
              AND ativo = 1
            """,
            (ator_id,),
        ).fetchone()

        if ator is None:
            raise ValueError("Administrador não autorizado.")

        # Impede a exclusão da própria conta.
        if usuario_id == ator_id:
            raise ValueError("Você não pode excluir sua própria conta.")

        # Consulta o cadastro que será excluído.
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

        # Protege o último administrador ativo.
        if usuario["perfil"] == "admin" and usuario["ativo"]:
            total_admins = conexao.execute("""
                SELECT COUNT(*)
                FROM usuarios
                WHERE perfil = 'admin'
                  AND ativo = 1
                """).fetchone()[0]

            if total_admins <= 1:
                raise ValueError("O último administrador ativo não pode ser excluído.")

        # Verifica os relacionamentos operacionais.
        vinculos = consultar_vinculos(conexao, "usuarios", usuario_id)

        if vinculos:
            raise ValueError(
                "Este usuário possui relacionamentos com "
                "outras tabelas. Utilize a desativação."
            )

        # Exclui o cadastro.
        try:
            conexao.execute(
                "DELETE FROM usuarios WHERE id = ?",
                (usuario_id,),
            )
        except sqlite3.IntegrityError as erro:
            raise ValueError(
                "Exclusão bloqueada por relacionamento no banco."
            ) from erro

        # Registra a operação na mesma transação.
        registrar_log(
            conexao,
            acao="excluir_usuario",
            usuario_id=ator["id"],
            usuario_login=ator["login"],
            entidade="usuarios",
            entidade_id=usuario_id,
            detalhes={
                "login_excluido": usuario["login"],
            },
        )
