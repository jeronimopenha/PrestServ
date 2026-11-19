import sqlite3
import json
from pathlib import Path
from datetime import date, datetime
from zoneinfo import ZoneInfo
from permissoes import exigir_permissao_usuario, tem_permissao

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


def pesquisar_pessoas(termo, ator_id):
    """
    Pesquisa pessoas ativas pelo nome.

    Retorna no máximo 30 resultados e respeita
    as permissões de acesso a dados pessoais.
    """

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_pessoas",
        )

        if not isinstance(termo, str):
            raise ValueError("Termo de pesquisa inválido.")

        termo = termo.strip()

        if not termo:
            return []

        # Para o porteiro, os campos sensíveis
        # sequer são selecionados do banco.
        if tem_permissao(
            perfil,
            "consultar_dados_sensiveis",
        ):
            colunas = "id, nome, documento, telefone"
        else:
            colunas = "id, nome, " "NULL AS documento, " "NULL AS telefone"

        registros = conexao.execute(
            f"""
            SELECT {colunas}
            FROM pessoas
            WHERE ativo = 1
              AND nome LIKE ? COLLATE NOCASE
            ORDER BY nome COLLATE NOCASE, id
            LIMIT 30
            """,
            (f"%{termo}%",),
        ).fetchall()

    return [dict(registro) for registro in registros]


def buscar_pessoa(pessoa_id, ator_id):
    """
    Consulta os dados de uma pessoa atendida.

    Retorna somente os campos autorizados para
    o papel do operador.
    """

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_pessoas",
        )

        if type(pessoa_id) is not int or pessoa_id <= 0:
            raise ValueError("Identificador da pessoa inválido.")

        registro = conexao.execute(
            """
            SELECT
                id,
                nome,
                documento,
                telefone,
                contato_nome,
                contato_telefone,
                ativo,
                criado_em
            FROM pessoas
            WHERE id = ?
            """,
            (pessoa_id,),
        ).fetchone()

    if registro is None:
        return None

    dados = dict(registro)

    # Oculta informações pessoais de operadores
    # sem permissão para consultar dados sensíveis.
    if not tem_permissao(
        perfil,
        "consultar_dados_sensiveis",
    ):
        for campo in (
            "documento",
            "telefone",
            "contato_nome",
            "contato_telefone",
        ):
            dados[campo] = None

    return dados


def listar_servicos(ator_id):
    """
    Retorna os serviços ativos para operadores autorizados.

    Exige permissão para consultar pessoas.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_pessoas",
        )

        registros = conexao.execute("""
            SELECT id, nome
            FROM servicos
            WHERE ativo = 1
            ORDER BY id
            """).fetchall()

    return [dict(registro) for registro in registros]


def buscar_servicos_presenca(presenca_id, ator_id):
    """
    Retorna os IDs dos serviços associados a uma presença.

    Porteiros podem consultar somente atendimentos
    da data atual. Os demais perfis autorizados
    podem consultar o histórico.
    """

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_pessoas",
        )

        if type(presenca_id) is not int or presenca_id <= 0:
            raise ValueError("Identificador da presença inválido.")

        # Recupera a data real da presença.
        # Não confia em uma data enviada pela interface.
        presenca = conexao.execute(
            """
            SELECT data
            FROM presencas
            WHERE id = ?
            """,
            (presenca_id,),
        ).fetchone()

        if presenca is None:
            return []

        data_presenca = date.fromisoformat(presenca["data"])
        hoje = date.fromisoformat(data_atual())

        if data_presenca > hoje:
            raise ValueError("Não é permitido consultar " "atendimentos futuros.")

        if perfil == "porteiro" and data_presenca != hoje:
            raise PermissionError(
                "O porteiro só pode consultar " "serviços da data atual."
            )

        registros = conexao.execute(
            """
            SELECT servico_id
            FROM presenca_servicos
            WHERE presenca_id = ?
            ORDER BY servico_id
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

    data = data_atual() if data is None else data
    servicos_ids = set(servicos_ids)

    # Valida a data informada.
    try:
        if not isinstance(data, str):
            raise ValueError()

        data_validada = date.fromisoformat(data)

        if data != data_validada.isoformat():
            raise ValueError()

    except ValueError:
        raise ValueError("Data de atendimento inválida.") from None

    hoje = date.fromisoformat(data_atual())

    # Não permite registrar atendimentos futuros.
    if data_validada > hoje:
        raise ValueError("Não é permitido registrar atendimentos futuros.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        # Verifica se o operador está ativo e autorizado.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "registrar_atendimento",
        )

        # Somente administradores podem alterar datas.
        if data_validada != hoje:
            exigir_permissao_usuario(
                conexao,
                ator_id,
                "alterar_data_atendimento",
            )

        # Obtém o login verdadeiro para a auditoria.
        ator = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        ator_login = ator["login"]

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


def total_presencas(data=None, ator_id=None):
    """
    Conta as presenças registradas em determinada data.

    Porteiros podem consultar somente a data atual.
    Administradores e secretaria podem consultar
    datas anteriores.
    """

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_pessoas",
        )

        data = data_atual() if data is None else data

        try:
            if not isinstance(data, str):
                raise ValueError()

            data_validada = date.fromisoformat(data)

            if data != data_validada.isoformat():
                raise ValueError()

        except ValueError:
            raise ValueError("Data de atendimento inválida.") from None

        hoje = date.fromisoformat(data_atual())

        if data_validada > hoje:
            raise ValueError("Não é permitido consultar " "atendimentos futuros.")

        if perfil == "porteiro" and data_validada != hoje:
            raise PermissionError(
                "O porteiro só pode consultar " "os totais da data atual."
            )

        resultado = conexao.execute(
            """
            SELECT COUNT(*) AS total
            FROM presencas
            WHERE data = ?
            """,
            (data,),
        ).fetchone()

    return resultado["total"]


def listar_pessoas(ator_id):
    """
    Lista pessoas ativas para seleção de atendimentos.

    Exige autorização e retorna somente ID e nome,
    sem expor documentos ou contatos pessoais.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_pessoas",
        )

        registros = conexao.execute("""
            SELECT id, nome
            FROM pessoas
            WHERE ativo = 1
            ORDER BY nome COLLATE NOCASE
        """).fetchall()

    return [dict(registro) for registro in registros]


def buscar_foto(pessoa_id, ator_id):
    """
    Consulta a fotografia de uma pessoa atendida.

    Retorna os bytes JPEG ou None quando não existe foto.
    Exige autorização para consultar fotografias.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_fotos",
        )

        if type(pessoa_id) is not int or pessoa_id <= 0:
            raise ValueError("Identificador da pessoa inválido.")

        registro = conexao.execute(
            """
            SELECT foto
            FROM fotos_pessoas
            WHERE pessoa_id = ?
            """,
            (pessoa_id,),
        ).fetchone()

    return registro["foto"] if registro else None


def salvar_foto(
    pessoa_id,
    foto_jpeg,
    ator_id=None,
    ator_login=None,
):
    """
    Salva ou substitui a fotografia de uma pessoa.

    Somente operadores autorizados a editar cadastros
    podem executar esta operação.
    """

    if type(pessoa_id) is not int or pessoa_id <= 0:
        raise ValueError("Identificador da pessoa inválido.")

    if not foto_jpeg:
        raise ValueError("Fotografia vazia.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        # Verifica a autorização diretamente no banco.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "editar_pessoas",
        )

        # Obtém o login verdadeiro do operador.
        ator = conexao.execute(
            """
            SELECT login
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

        pessoa = conexao.execute(
            """
            SELECT id
            FROM pessoas
            WHERE id = ?
            """,
            (pessoa_id,),
        ).fetchone()

        if pessoa is None:
            raise ValueError("Pessoa não encontrada.")

        # Verifica se já existe uma fotografia.
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

        # Insere ou substitui a fotografia.
        conexao.execute(
            """
            INSERT INTO fotos_pessoas (
                pessoa_id,
                foto,
                formato,
                atualizada_em
            )
            VALUES (?, ?, 'image/jpeg', CURRENT_TIMESTAMP)

            ON CONFLICT(pessoa_id)
            DO UPDATE SET
                foto = excluded.foto,
                formato = 'image/jpeg',
                atualizada_em = CURRENT_TIMESTAMP
            """,
            (pessoa_id, foto_jpeg),
        )

        # Registra a operação sem incluir a imagem no log.
        registrar_log(
            conexao,
            acao=("substituir_foto" if foto_existente else "adicionar_foto"),
            usuario_id=ator_id,
            usuario_login=ator["login"],
            entidade="fotos_pessoas",
            entidade_id=pessoa_id,
        )


def remover_foto(
    pessoa_id,
    ator_id=None,
    ator_login=None,
):
    """
    Remove a fotografia de uma pessoa atendida.

    Exige permissão para editar cadastros.
    Registra a remoção na auditoria.
    """

    if type(pessoa_id) is not int or pessoa_id <= 0:
        raise ValueError("Identificador da pessoa inválido.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        # Autoriza a operação diretamente no banco.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "editar_pessoas",
        )

        # Identifica o verdadeiro operador.
        ator = conexao.execute(
            """
            SELECT login
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

        # Remove a fotografia, se existir.
        cursor = conexao.execute(
            """
            DELETE FROM fotos_pessoas
            WHERE pessoa_id = ?
            """,
            (pessoa_id,),
        )

        # Nenhuma fotografia removida: não registra log.
        if cursor.rowcount == 0:
            return

        registrar_log(
            conexao,
            acao="remover_foto",
            usuario_id=ator_id,
            usuario_login=ator["login"],
            entidade="fotos_pessoas",
            entidade_id=pessoa_id,
        )


def listar_pessoas_admin(ator_id):
    """
    Lista pessoas ativas e inativas com dados cadastrais.

    Acesso exclusivo a operadores autorizados
    a consultar pessoas e dados sensíveis.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_pessoas",
        )

        exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_dados_sensiveis",
        )

        registros = conexao.execute("""
            SELECT
                id,
                nome,
                documento,
                telefone,
                contato_nome,
                contato_telefone,
                ativo,
                criado_em
            FROM pessoas
            ORDER BY nome COLLATE NOCASE, id
        """).fetchall()

    return [dict(registro) for registro in registros]


def cadastrar_pessoa(
    nome,
    documento=None,
    telefone=None,
    contato_nome=None,
    contato_telefone=None,
    ator_id=None,
    ator_login=None,
):
    """Cadastra uma pessoa atendida, verificando a autorização."""

    nome = nome.strip()

    if not nome:
        raise ValueError("O nome é obrigatório.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        # Verifica a autorização diretamente no banco.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "cadastrar_pessoas",
        )

        # Obtém o login verdadeiro do responsável.
        ator = conexao.execute(
            """
            SELECT login
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

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
            usuario_login=ator["login"],
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
    """Atualiza uma pessoa, verificando a autorização."""

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
        conexao.execute("BEGIN IMMEDIATE")

        # Verifica a autorização diretamente no SQLite.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "editar_pessoas",
        )

        # Obtém o login verdadeiro do operador.
        ator = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

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
                # Não registra documentos ou telefones nos logs.
                alteracoes[campo] = {
                    "antes_preenchido": bool(valor_antigo),
                    "depois_preenchido": bool(valor_novo),
                }

        # Se nada mudou, não grava nem registra log.
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
            usuario_login=ator["login"],
            entidade="pessoas",
            entidade_id=pessoa_id,
            detalhes={"alteracoes": alteracoes},
        )


def alterar_status_pessoa(
    pessoa_id,
    ativo,
    ator_id,
    ator_login=None,
):
    """
    Ativa ou desativa uma pessoa atendida.

    Exige permissão para editar cadastros.
    Preserva o histórico e registra as alterações.
    """

    if type(pessoa_id) is not int or pessoa_id <= 0:
        raise ValueError("Identificador da pessoa inválido.")

    novo_status = int(bool(ativo))

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        # Autoriza a operação consultando o banco.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "editar_pessoas",
        )

        # Identifica o verdadeiro operador.
        ator = conexao.execute(
            """
            SELECT login
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

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

        # Não registra operações sem alteração.
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
            usuario_login=ator["login"],
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

        # Verifica a autorização diretamente no banco.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "excluir_pessoas",
        )

        # Obtém os dados reais do responsável pela exclusão.
        ator = conexao.execute(
            """
            SELECT id, login
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

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
        # Verifica a autorização diretamente no banco.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_logs",
        )

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
        # Somente superadministradores ativos.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_logs",
        )

        registros = conexao.execute("""
            SELECT DISTINCT acao
            FROM logs
            ORDER BY acao COLLATE NOCASE
        """).fetchall()

    return [registro["acao"] for registro in registros]


def excluir_logs(ids, ator_id):
    """Exclui logs selecionados e registra a operação."""

    if not isinstance(ids, (list, tuple, set)):
        raise ValueError("Seleção de logs inválida.")

    ids = sorted(set(ids))

    if not ids:
        raise ValueError("Nenhum log selecionado.")

    if len(ids) > 500:
        raise ValueError("Selecione no máximo 500 logs por operação.")

    if any(type(id) is not int or id <= 0 for id in ids):
        raise ValueError("Identificadores de logs inválidos.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        # Confere se o operador é administrador ativo.
        # Somente superadministradores ativos podem excluir logs.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "excluir_logs",
        )

        # Identifica o responsável para registrar a auditoria.
        ator = conexao.execute(
            """
            SELECT id, login
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

        marcadores = ",".join("?" for _ in ids)

        # Confere se todos os registros ainda existem.
        encontrados = conexao.execute(
            f"""
            SELECT id
            FROM logs
            WHERE id IN ({marcadores})
            """,
            ids,
        ).fetchall()

        if len(encontrados) != len(ids):
            raise ValueError(
                "A seleção está desatualizada. " "Atualize a página e tente novamente."
            )

        # Exclui somente os logs selecionados.
        cursor = conexao.execute(
            f"""
            DELETE FROM logs
            WHERE id IN ({marcadores})
            """,
            ids,
        )

        quantidade = cursor.rowcount

        # Registra a limpeza na mesma transação.
        registrar_log(
            conexao,
            acao="excluir_logs",
            usuario_id=ator["id"],
            usuario_login=ator["login"],
            entidade="logs",
            detalhes={
                "quantidade": quantidade,
                "ids_excluidos": ids,
            },
        )

    return quantidade


def buscar_presenca(pessoa_id, data=None, ator_id=None):
    """
    Consulta a presença de uma pessoa em determinada data.

    O porteiro pode consultar apenas a data atual.
    Administradores e secretaria podem consultar
    datas anteriores.
    """

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_pessoas",
        )

        if type(pessoa_id) is not int or pessoa_id <= 0:
            raise ValueError("Identificador da pessoa inválido.")

        data = data_atual() if data is None else data

        try:
            if not isinstance(data, str):
                raise ValueError()

            data_validada = date.fromisoformat(data)

            if data != data_validada.isoformat():
                raise ValueError()

        except ValueError:
            raise ValueError("Data de atendimento inválida.") from None

        hoje = date.fromisoformat(data_atual())

        if data_validada > hoje:
            raise ValueError("Não é permitido consultar atendimentos futuros.")

        if perfil == "porteiro" and data_validada != hoje:
            raise PermissionError(
                "O porteiro só pode consultar " "atendimentos da data atual."
            )

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
