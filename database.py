
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
        raise FileNotFoundError(
            f"Banco de dados não encontrado: {DB_PATH}"
        )

    conexao = sqlite3.connect(
        DB_PATH,
        timeout=10
    )

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
            (f"%{termo}%",)
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
            (pessoa_id,)
        ).fetchone()

    return dict(registro) if registro else None


def listar_servicos():
    """Retorna os serviços ativos."""
    with conectar() as conexao:
        registros = conexao.execute(
            """
            SELECT id, nome
            FROM servicos
            WHERE ativo = 1
            ORDER BY id
            """
        ).fetchall()

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
            (pessoa_id, data)
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
            (presenca_id,)
        ).fetchall()

    return [registro["servico_id"] for registro in registros]


def salvar_atendimento(pessoa_id, servicos_ids):
    """
    Registra uma presença ou atualiza seus serviços.

    Garante uma única presença por pessoa por dia.
    """
    data = data_atual()
    servicos_ids = set(servicos_ids)

    with conectar() as conexao:
        pessoa = conexao.execute(
            """
            SELECT id
            FROM pessoas
            WHERE id = ? AND ativo = 1
            """,
            (pessoa_id,)
        ).fetchone()

        if pessoa is None:
            raise ValueError("Pessoa não encontrada ou inativa.")

        # Cria a presença somente se ainda não existir.
        conexao.execute(
            """
            INSERT INTO presencas (pessoa_id, data)
            VALUES (?, ?)
            ON CONFLICT(pessoa_id, data) DO NOTHING
            """,
            (pessoa_id, data)
        )

        presenca = conexao.execute(
            """
            SELECT id
            FROM presencas
            WHERE pessoa_id = ? AND data = ?
            """,
            (pessoa_id, data)
        ).fetchone()

        presenca_id = presenca["id"]

        # Confere se todos os serviços selecionados são válidos.
        servicos_validos = {
            registro["id"]
            for registro in conexao.execute(
                "SELECT id FROM servicos WHERE ativo = 1"
            ).fetchall()
        }

        if not servicos_ids.issubset(servicos_validos):
            raise ValueError("Um ou mais serviços são inválidos.")

        # Substitui a seleção anterior pela atual.
        conexao.execute(
            """
            DELETE FROM presenca_servicos
            WHERE presenca_id = ?
            """,
            (presenca_id,)
        )

        conexao.executemany(
            """
            INSERT INTO presenca_servicos
                (presenca_id, servico_id)
            VALUES (?, ?)
            """,
            [
                (presenca_id, servico_id)
                for servico_id in servicos_ids
            ]
        )

    return presenca_id


def total_presencas_hoje():
    """Retorna a quantidade de pessoas atendidas hoje."""
    with conectar() as conexao:
        resultado = conexao.execute(
            """
            SELECT COUNT(*) AS total
            FROM presencas
            WHERE data = ?
            """,
            (data_atual(),)
        ).fetchone()

    return resultado["total"]
