import sqlite3
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "dados" / "PrestServ.db"

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


def registrar_log(
    conexao,
    acao,
    usuario_id=None,
    usuario_login=None,
    entidade=None,
    entidade_id=None,
    resultado="sucesso",
    detalhes=None,
):
    """Registra uma operação no histórico do sistema."""

    detalhes_json = (
        json.dumps(detalhes, ensure_ascii=False) if detalhes is not None else None
    )

    conexao.execute(
        """
        INSERT INTO logs (
            usuario_id,
            usuario_login,
            acao,
            entidade,
            entidade_id,
            resultado,
            detalhes_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            usuario_id,
            usuario_login,
            acao,
            entidade,
            entidade_id,
            resultado,
            detalhes_json,
        ),
    )


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


def salvar_atendimento(
    pessoa_id, servicos_ids, data=None, ator_id=None, ator_login=None
):
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

        presenca_existia = presenca is not None

        servicos_anteriores = []

        if presenca_existia:
            servicos_anteriores = sorted(
                registro["servico_id"]
                for registro in conexao.execute(
                    """
                    SELECT servico_id
                    FROM presenca_servicos
                    WHERE presenca_id = ?
                    """,
                    (presenca["id"],),
                ).fetchall()
            )

        # Nenhum serviço selecionado: remove a presença.
        if not servicos_ids:
            if presenca_existia:
                conexao.execute(
                    "DELETE FROM presencas WHERE id = ?",
                    (presenca["id"],),
                )

                registrar_log(
                    conexao,
                    acao="remover_atendimento",
                    usuario_id=ator_id,
                    usuario_login=ator_login,
                    entidade="presencas",
                    entidade_id=presenca["id"],
                    detalhes={
                        "pessoa_id": pessoa_id,
                        "data": data,
                        "servicos_anteriores": servicos_anteriores,
                        "servicos_novos": [],
                    },
                )

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

        servicos_novos = sorted(servicos_ids)

        if presenca_existia and servicos_anteriores == servicos_novos:
            return presenca["id"]

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

        registrar_log(
            conexao,
            acao=("atualizar_atendimento" if presenca_existia else "criar_atendimento"),
            usuario_id=ator_id,
            usuario_login=ator_login,
            entidade="presencas",
            entidade_id=presenca_id,
            detalhes={
                "pessoa_id": pessoa_id,
                "data": data,
                "servicos_anteriores": servicos_anteriores,
                "servicos_novos": servicos_novos,
            },
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


def salvar_foto(pessoa_id, foto_jpeg, ator_id=None, ator_login=None):
    """Salva ou substitui a fotografia de uma pessoa."""
    if not foto_jpeg:
        raise ValueError("Fotografia vazia.")

    with conectar() as conexao:
        pessoa = conexao.execute(
            "SELECT id FROM pessoas WHERE id = ?", (pessoa_id,)
        ).fetchone()

        if pessoa is None:
            raise ValueError("Pessoa não encontrada.")

        foto_existente = (
            conexao.execute(
                """
                SELECT 1
                FROM fotos_pessoas
                WHERE pessoa_id = ?
                """,
                (pessoa_id,),
            ).fetchone()
            is not None
        )

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
        registrar_log(
            conexao,
            acao=("substituir_foto" if foto_existente else "adicionar_foto"),
            usuario_id=ator_id,
            usuario_login=ator_login,
            entidade="fotos_pessoas",
            entidade_id=pessoa_id,
        )


def remover_foto(pessoa_id, ator_id=None, ator_login=None):
    """Remove a fotografia e registra a operação."""

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            DELETE FROM fotos_pessoas
            WHERE pessoa_id = ?
            """,
            (pessoa_id,),
        )

        # Só registra se uma fotografia foi realmente removida.
        if cursor.rowcount > 0:
            registrar_log(
                conexao,
                acao="remover_foto",
                usuario_id=ator_id,
                usuario_login=ator_login,
                entidade="fotos_pessoas",
                entidade_id=pessoa_id,
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
    nome,
    documento=None,
    telefone=None,
    contato_nome=None,
    contato_telefone=None,
    ator_id=None,
    ator_login=None,
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

        pessoa_id = cursor.lastrowid

        registrar_log(
            conexao,
            acao="cadastrar_pessoa",
            usuario_id=ator_id,
            usuario_login=ator_login,
            entidade="pessoas",
            entidade_id=pessoa_id,
        )

        return pessoa_id


def atualizar_pessoa(
    pessoa_id,
    nome,
    documento=None,
    telefone=None,
    contato_nome=None,
    contato_telefone=None,
    ator_id=None,
    ator_login=None,
):
    nome = nome.strip()

    if not nome:
        raise ValueError("O nome é obrigatório.")

    novos_dados = {
        "nome": nome,
        "documento": documento.strip() or None if documento else None,
        "telefone": telefone.strip() or None if telefone else None,
        "contato_nome": contato_nome.strip() or None if contato_nome else None,
        "contato_telefone": (
            contato_telefone.strip() or None if contato_telefone else None
        ),
    }

    with conectar() as conexao:
        anterior = conexao.execute(
            """
            SELECT nome, documento, telefone,
                   contato_nome, contato_telefone
            FROM pessoas
            WHERE id = ?
            """,
            (pessoa_id,),
        ).fetchone()

        if anterior is None:
            raise ValueError("Pessoa não encontrada.")

        alteracoes = {}

        for campo, valor_novo in novos_dados.items():
            valor_antigo = anterior[campo]

            if valor_antigo != valor_novo:
                alteracoes[campo] = {
                    "antes_preenchido": bool(valor_antigo),
                    "depois_preenchido": bool(valor_novo),
                }

        # Nada mudou: não precisa atualizar nem registrar log.
        if not alteracoes:
            return

        conexao.execute(
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
                novos_dados["nome"],
                novos_dados["documento"],
                novos_dados["telefone"],
                novos_dados["contato_nome"],
                novos_dados["contato_telefone"],
                pessoa_id,
            ),
        )

        registrar_log(
            conexao,
            acao="atualizar_pessoa",
            usuario_id=ator_id,
            usuario_login=ator_login,
            entidade="pessoas",
            entidade_id=pessoa_id,
            detalhes={"alteracoes": alteracoes},
        )


def alterar_status_pessoa(pessoa_id, ativo, ator_id, ator_login):
    """Ativa ou desativa uma pessoa, registrando a operação."""

    novo_status = int(bool(ativo))

    with conectar() as conexao:
        pessoa = conexao.execute(
            """
            SELECT ativo
            FROM pessoas
            WHERE id = ?
            """,
            (pessoa_id,),
        ).fetchone()

        if pessoa is None:
            raise ValueError("Pessoa não encontrada.")

        status_anterior = pessoa["ativo"]

        # Não registra nada quando o status não muda.
        if status_anterior == novo_status:
            return

        conexao.execute(
            """
            UPDATE pessoas
            SET ativo = ?
            WHERE id = ?
            """,
            (novo_status, pessoa_id),
        )

        registrar_log(
            conexao,
            acao=("ativar_pessoa" if novo_status else "desativar_pessoa"),
            usuario_id=ator_id,
            usuario_login=ator_login,
            entidade="pessoas",
            entidade_id=pessoa_id,
            detalhes={
                "ativo_anterior": bool(status_anterior),
                "ativo_novo": bool(novo_status),
            },
        )


def excluir_pessoa(pessoa_id, ator_id):
    """Exclui uma pessoa somente se não possuir relacionamentos."""

    from estrutura_v110 import consultar_vinculos

    if type(pessoa_id) is not int or pessoa_id <= 0:
        raise ValueError("Identificador da pessoa inválido.")

    with conectar() as conexao:
        # Bloqueia outras escritas até o fim da operação.
        conexao.execute("BEGIN IMMEDIATE")

        # Verifica se o operador é um administrador ativo.
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

        pessoa = conexao.execute(
            "SELECT id FROM pessoas WHERE id = ?",
            (pessoa_id,),
        ).fetchone()

        if pessoa is None:
            raise ValueError("Pessoa não encontrada.")

        # Verifica os relacionamentos dentro da transação.
        vinculos = consultar_vinculos(conexao, "pessoas", pessoa_id)

        if vinculos:
            tabelas = ", ".join(v["tabela"] for v in vinculos)

            raise ValueError(
                "Esta pessoa não pode ser excluída porque "
                f"possui relacionamentos em: {tabelas}. "
                "Utilize a desativação."
            )

        # Tenta excluir. As chaves estrangeiras continuam ativas.
        try:
            conexao.execute(
                "DELETE FROM pessoas WHERE id = ?",
                (pessoa_id,),
            )
        except sqlite3.IntegrityError as erro:
            raise ValueError(
                "Exclusão bloqueada por relacionamento no banco."
            ) from erro

        # Registra a exclusão na mesma transação.
        registrar_log(
            conexao,
            acao="excluir_pessoa",
            usuario_id=ator["id"],
            usuario_login=ator["login"],
            entidade="pessoas",
            entidade_id=pessoa_id,
        )


def listar_logs(
    ator_id,
    limite=200,
    inicio=None,
    fim=None,
    operador=None,
    acao=None,
    resultado=None,
):
    """Consulta os logs com filtros, apenas para administradores."""

    if type(limite) is not int or not 1 <= limite <= 1000:
        raise ValueError("Limite de registros inválido.")

    with conectar() as conexao:
        # Verifica a permissão do operador.
        ator = conexao.execute(
            """
            SELECT id
            FROM usuarios
            WHERE id = ?
              AND perfil = 'admin'
              AND ativo = 1
            """,
            (ator_id,),
        ).fetchone()

        if ator is None:
            raise PermissionError("Somente administradores podem consultar os logs.")

        filtros = []
        parametros = []

        if inicio:
            filtros.append("criado_em >= ?")
            parametros.append(inicio)

        if fim:
            filtros.append("criado_em < ?")
            parametros.append(fim)

        if operador:
            filtros.append("usuario_login LIKE ? COLLATE NOCASE")
            parametros.append(f"%{operador.strip()}%")

        if acao:
            filtros.append("acao = ?")
            parametros.append(acao)

        if resultado:
            filtros.append("resultado = ?")
            parametros.append(resultado)

        where = "WHERE " + " AND ".join(filtros) if filtros else ""

        sql = f"""
            SELECT
                id,
                criado_em,
                usuario_id,
                usuario_login,
                acao,
                entidade,
                entidade_id,
                resultado,
                detalhes_json
            FROM logs
            {where}
            ORDER BY id DESC
            LIMIT ?
        """

        parametros.append(limite)

        registros = conexao.execute(sql, parametros).fetchall()

    return [dict(registro) for registro in registros]


def listar_acoes_logs(ator_id):
    """Lista as ações existentes nos logs."""

    with conectar() as conexao:
        ator = conexao.execute(
            """
            SELECT id
            FROM usuarios
            WHERE id = ?
              AND perfil = 'admin'
              AND ativo = 1
            """,
            (ator_id,),
        ).fetchone()

        if ator is None:
            raise PermissionError("Somente administradores podem consultar os logs.")

        registros = conexao.execute("""
            SELECT DISTINCT acao
            FROM logs
            ORDER BY acao COLLATE NOCASE
            """).fetchall()

    return [registro["acao"] for registro in registros]
