import sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "dados" / "PrestServ.db"
print(DB_PATH)

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")


def data_atual():
    """Retorna a data atual no fuso horário de Brasília."""
    return datetime.now(FUSO_HORARIO).date().isoformat()


def conectar():
    """Abre uma conexão com o banco SQLite."""
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Banco de dados não encontrado: {DB_PATH}")

    conexao = sqlite3.connect(DB_PATH, timeout=10)

    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


def pesquisar_pessoas(termo):
    """Pesquisa pessoas ativas pelo nome."""
    termo = termo.strip()

    if not termo:
        return []

    with conectar() as conexao:
        registros = conexao.execute(
            """
            SELECT id, nome, documento, telefone
            FROM pessoas
            WHERE ativo = 1
              AND nome LIKE ? COLLATE NOCASE
            ORDER BY nome
            LIMIT 30
            """,
            (f"%{termo}%",),
        ).fetchall()

    return [dict(registro) for registro in registros]


def buscar_pessoa(pessoa_id):
    """Retorna os dados de uma pessoa."""
    with conectar() as conexao:
        registro = conexao.execute(
            """
            SELECT *
            FROM pessoas
            WHERE id = ?
            """,
            (pessoa_id,),
        ).fetchone()

    return dict(registro) if registro else None


def listar_servicos():
    """Retorna os serviços ativos."""
    with conectar() as conexao:
        registros = conexao.execute("""
            SELECT id, nome
            FROM servicos
            WHERE ativo = 1
            ORDER BY id
            """).fetchall()

    return [dict(registro) for registro in registros]


def buscar_presenca(pessoa_id, data=None):
    """Consulta a presença de uma pessoa em determinada data."""
    data = data or data_atual()

    with conectar() as conexao:
        registro = conexao.execute(
            """
            SELECT id, pessoa_id, data
            FROM presencas
            WHERE pessoa_id = ?
              AND data = ?
            """,
            (pessoa_id, data),
        ).fetchone()

    return dict(registro) if registro else None


def buscar_servicos_presenca(presenca_id):
    """Retorna os IDs dos serviços associados à presença."""
    with conectar() as conexao:
        registros = conexao.execute(
            """
            SELECT servico_id
            FROM presenca_servicos
            WHERE presenca_id = ?
            """,
            (presenca_id,),
        ).fetchall()

    return [registro["servico_id"] for registro in registros]


def salvar_atendimento(pessoa_id, servicos_ids, data=None):
    """
    Registra, atualiza ou remove um atendimento.

    - Com serviços: cria ou atualiza a presença.
    - Sem serviços: remove a presença, se existir.
    """
    data = data or data_atual()
    servicos_ids = set(servicos_ids)

    with conectar() as conexao:
        pessoa = conexao.execute(
            """
            SELECT id
            FROM pessoas
            WHERE id = ? AND ativo = 1
            """,
            (pessoa_id,),
        ).fetchone()

        if pessoa is None:
            raise ValueError("Pessoa não encontrada ou inativa.")

        presenca = conexao.execute(
            """
            SELECT id
            FROM presencas
            WHERE pessoa_id = ? AND data = ?
            """,
            (pessoa_id, data),
        ).fetchone()

        # Nenhum serviço selecionado: remove a presença.
        if not servicos_ids:
            if presenca:
                conexao.execute("DELETE FROM presencas WHERE id = ?", (presenca["id"],))
            return None

        # Valida os serviços antes de gravar.
        servicos_validos = {
            registro["id"]
            for registro in conexao.execute(
                "SELECT id FROM servicos WHERE ativo = 1"
            ).fetchall()
        }

        if not servicos_ids.issubset(servicos_validos):
            raise ValueError("Um ou mais serviços são inválidos.")

        # Cria a presença caso ainda não exista.
        conexao.execute(
            """
            INSERT INTO presencas (pessoa_id, data)
            VALUES (?, ?)
            ON CONFLICT(pessoa_id, data) DO NOTHING
            """,
            (pessoa_id, data),
        )

        presenca = conexao.execute(
            """
            SELECT id
            FROM presencas
            WHERE pessoa_id = ? AND data = ?
            """,
            (pessoa_id, data),
        ).fetchone()

        presenca_id = presenca["id"]

        # Atualiza os serviços utilizados.
        conexao.execute(
            """
            DELETE FROM presenca_servicos
            WHERE presenca_id = ?
            """,
            (presenca_id,),
        )

        conexao.executemany(
            """
            INSERT INTO presenca_servicos
                (presenca_id, servico_id)
            VALUES (?, ?)
            """,
            [(presenca_id, servico_id) for servico_id in servicos_ids],
        )

    return presenca_id


def total_presencas(data=None):
    """Conta as presenças registradas na data informada."""
    data = data or data_atual()

    with conectar() as conexao:
        resultado = conexao.execute(
            """
            SELECT COUNT(*) AS total
            FROM presencas
            WHERE data = ?
            """,
            (data,),
        ).fetchone()

    return resultado["total"]


def listar_pessoas():
    """Lista todas as pessoas ativas em ordem alfabética."""
    with conectar() as conexao:
        registros = conexao.execute("""
            SELECT id, nome, documento
            FROM pessoas
            WHERE ativo = 1
            ORDER BY nome COLLATE NOCASE
            """).fetchall()

    return [dict(registro) for registro in registros]


def buscar_foto(pessoa_id):
    """Retorna os bytes JPEG da fotografia ou None."""
    with conectar() as conexao:
        registro = conexao.execute(
            """
            SELECT foto
            FROM fotos_pessoas
            WHERE pessoa_id = ?
            """,
            (pessoa_id,),
        ).fetchone()

    return registro["foto"] if registro else None


def salvar_foto(pessoa_id, foto_jpeg):
    """Salva ou substitui a fotografia de uma pessoa."""
    if not foto_jpeg:
        raise ValueError("Fotografia vazia.")

    with conectar() as conexao:
        pessoa = conexao.execute(
            "SELECT id FROM pessoas WHERE id = ?", (pessoa_id,)
        ).fetchone()

        if pessoa is None:
            raise ValueError("Pessoa não encontrada.")

        conexao.execute(
            """
            INSERT INTO fotos_pessoas
                (pessoa_id, foto, formato, atualizada_em)
            VALUES (?, ?, 'image/jpeg', CURRENT_TIMESTAMP)
            ON CONFLICT(pessoa_id)
            DO UPDATE SET
                foto = excluded.foto,
                formato = 'image/jpeg',
                atualizada_em = CURRENT_TIMESTAMP
            """,
            (pessoa_id, foto_jpeg),
        )


def remover_foto(pessoa_id):
    """Remove a fotografia de uma pessoa."""
    with conectar() as conexao:
        conexao.execute(
            """
            DELETE FROM fotos_pessoas
            WHERE pessoa_id = ?
            """,
            (pessoa_id,),
        )


def listar_pessoas_admin():
    """Lista pessoas ativas e inativas."""
    with conectar() as conexao:
        registros = conexao.execute("""
            SELECT id, nome, documento, telefone,
                   contato_nome, contato_telefone,
                   ativo, criado_em
            FROM pessoas
            ORDER BY nome COLLATE NOCASE, id
            """).fetchall()

    return [dict(r) for r in registros]


def cadastrar_pessoa(
    nome, documento=None, telefone=None, contato_nome=None, contato_telefone=None
):
    nome = nome.strip()

    if not nome:
        raise ValueError("O nome é obrigatório.")

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO pessoas (
                nome, documento, telefone,
                contato_nome, contato_telefone
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                nome,
                documento.strip() or None if documento else None,
                telefone.strip() or None if telefone else None,
                contato_nome.strip() or None if contato_nome else None,
                contato_telefone.strip() or None if contato_telefone else None,
            ),
        )

        return cursor.lastrowid


def atualizar_pessoa(
    pessoa_id,
    nome,
    documento=None,
    telefone=None,
    contato_nome=None,
    contato_telefone=None,
):
    nome = nome.strip()

    if not nome:
        raise ValueError("O nome é obrigatório.")

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE pessoas
            SET nome = ?,
                documento = ?,
                telefone = ?,
                contato_nome = ?,
                contato_telefone = ?
            WHERE id = ?
            """,
            (
                nome,
                documento.strip() or None if documento else None,
                telefone.strip() or None if telefone else None,
                contato_nome.strip() or None if contato_nome else None,
                contato_telefone.strip() or None if contato_telefone else None,
                pessoa_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError("Pessoa não encontrada.")


def alterar_status_pessoa(pessoa_id, ativo):
    """Ativa ou desativa uma pessoa sem apagar seu histórico."""
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE pessoas
            SET ativo = ?
            WHERE id = ?
            """,
            (int(bool(ativo)), pessoa_id),
        )

        if cursor.rowcount == 0:
            raise ValueError("Pessoa não encontrada.")
