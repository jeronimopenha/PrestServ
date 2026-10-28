import hashlib
import hmac
import secrets

from database import conectar
from common import ITERACOES, TAM_SENHA


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
    with conectar() as conexao:
        usuario = conexao.execute(
            """
            SELECT id, nome, login, senha_hash, perfil
            FROM usuarios
            WHERE login = ? AND ativo = 1
            """,
            (login.strip(),),
        ).fetchone()

    if usuario is None:
        return None

    if not verificar_senha(senha, usuario["senha_hash"]):
        return None

    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "login": usuario["login"],
        "perfil": usuario["perfil"],
    }


def criar_usuario(nome, login, senha, perfil):
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

        return cursor.lastrowid


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


def redefinir_senha(usuario_id, nova_senha):
    senha_hash = gerar_hash(nova_senha)

    with conectar() as conexao:
        conexao.execute(
            "UPDATE usuarios SET senha_hash = ? WHERE id = ?", (senha_hash, usuario_id)
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
            SELECT id, perfil, ativo
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

        conexao.execute(
            """
            UPDATE usuarios
            SET nome = ?, login = ?, perfil = ?
            WHERE id = ?
            """,
            (nome, login, perfil, usuario_id),
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

        conexao.execute(
            """
            UPDATE usuarios
            SET ativo = ?
            WHERE id = ?
            """,
            (int(bool(ativo)), usuario_id),
        )
