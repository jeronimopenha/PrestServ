import pandas as pd
from conn.database import conectar, _tem_coluna_quantidade_servico
from datetime import date
from security.permissoes import exigir_permissao_usuario


def presencas_detalhadas(inicio, fim, pessoa_id=None, ator_id=None):
    """
    Consulta atendimentos individuais de um período.

    Exige permissão para relatórios pessoais,
    mesmo sem filtro por pessoa.

    Compatível com SQLite V1, V2 e V3.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_pessoais",
        )

        # Validação do período.
        try:
            if not isinstance(inicio, str) or not isinstance(fim, str):
                raise ValueError()

            data_inicio = date.fromisoformat(inicio)
            data_fim = date.fromisoformat(fim)

            if inicio != data_inicio.isoformat() or fim != data_fim.isoformat():
                raise ValueError()

        except ValueError:
            raise ValueError("Período do relatório inválido.") from None

        if data_inicio > data_fim:
            raise ValueError("A data inicial não pode superar a final.")

        parametros = [inicio, fim]
        filtro = ""

        if pessoa_id is not None:
            if type(pessoa_id) is not int or pessoa_id <= 0:
                raise ValueError("Identificador da pessoa inválido.")

            filtro = "AND p.pessoa_id = ?"
            parametros.append(pessoa_id)

        # V1/V2: cada vínculo representa uma unidade.
        # V3: utiliza a quantidade efetiva.
        expressao_unidades = (
            "ps.quantidade" if _tem_coluna_quantidade_servico(conexao) else "1"
        )

        resultado = pd.read_sql_query(
            f"""
            SELECT
                p.id AS presenca_id,
                p.data AS data,
                pe.id AS pessoa_id,
                pe.nome AS pessoa,

                COALESCE(
                    GROUP_CONCAT(s.nome, ', '),
                    ''
                ) AS servicos,

                COUNT(s.id) AS quantidade_servicos,

                COALESCE(
                    SUM(
                        CASE
                            WHEN s.id IS NOT NULL
                            THEN {expressao_unidades}
                            ELSE 0
                        END
                    ),
                    0
                ) AS unidades_servicos,

                p.criado_em AS registrado_em

            FROM presencas p

            JOIN pessoas pe
                ON pe.id = p.pessoa_id

            LEFT JOIN presenca_servicos ps
                ON ps.presenca_id = p.id

            LEFT JOIN servicos s
                ON s.id = ps.servico_id

            WHERE p.data BETWEEN ? AND ?
            {filtro}

            GROUP BY
                p.id,
                p.data,
                pe.id,
                pe.nome,
                p.criado_em

            ORDER BY p.data DESC, pe.nome
            """,
            conexao,
            params=parametros,
        )

    return resultado


def servicos_por_tipo(inicio, fim, pessoa_id=None, ator_id=None):
    """
    Retorna os serviços registrados e as unidades distribuídas.

    Relatórios gerais: superadmin, admin e consulta.
    Filtro individual: somente superadmin e admin.

    Compatível com SQLite V1, V2 e V3.
    """

    with conectar() as conexao:
        # Verifica a permissão antes de consultar os dados.
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_gerais",
        )

        if pessoa_id is not None:
            exigir_permissao_usuario(
                conexao,
                ator_id,
                "relatorios_pessoais",
            )

            if type(pessoa_id) is not int or pessoa_id <= 0:
                raise ValueError("Identificador da pessoa inválido.")

        # Valida o período.
        try:
            if not isinstance(inicio, str) or not isinstance(fim, str):
                raise ValueError()

            data_inicio = date.fromisoformat(inicio)
            data_fim = date.fromisoformat(fim)

            if inicio != data_inicio.isoformat() or fim != data_fim.isoformat():
                raise ValueError()

        except ValueError:
            raise ValueError("Período do relatório inválido.") from None

        if data_inicio > data_fim:
            raise ValueError("A data inicial não pode superar a final.")

        parametros = [inicio, fim]
        filtro = ""

        if pessoa_id is not None:
            filtro = "AND p.pessoa_id = ?"
            parametros.append(pessoa_id)

        # V1/V2: cada serviço registrado vale uma unidade.
        # V3: utiliza a quantidade efetivamente distribuída.
        expressao_unidades = (
            "ps.quantidade" if _tem_coluna_quantidade_servico(conexao) else "1"
        )

        resultado = pd.read_sql_query(
            f"""
            SELECT
                s.nome AS servico,

                COUNT(*) AS quantidade,

                COALESCE(
                    SUM({expressao_unidades}),
                    0
                ) AS unidades

            FROM presenca_servicos ps

            JOIN servicos s
                ON s.id = ps.servico_id

            JOIN presencas p
                ON p.id = ps.presenca_id

            WHERE p.data BETWEEN ? AND ?
            {filtro}

            GROUP BY s.id, s.nome

            ORDER BY quantidade DESC, s.nome
            """,
            conexao,
            params=parametros,
        )

    return resultado


def frequencia_pessoas(inicio, fim, pessoa_id=None, ator_id=None):
    """
    Retorna a frequência individual das pessoas atendidas.

    Acesso exclusivo a superadmin e admin,
    mesmo sem filtro por pessoa.

    Compatível com SQLite V1, V2 e V3.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_pessoais",
        )

        # Validação do período.
        try:
            if not isinstance(inicio, str) or not isinstance(fim, str):
                raise ValueError()

            data_inicio = date.fromisoformat(inicio)
            data_fim = date.fromisoformat(fim)

            if inicio != data_inicio.isoformat() or fim != data_fim.isoformat():
                raise ValueError()

        except ValueError:
            raise ValueError("Período do relatório inválido.") from None

        if data_inicio > data_fim:
            raise ValueError("A data inicial não pode superar a final.")

        parametros = [inicio, fim]
        filtro = ""

        if pessoa_id is not None:
            if type(pessoa_id) is not int or pessoa_id <= 0:
                raise ValueError("Identificador da pessoa inválido.")

            filtro = "AND pe.id = ?"
            parametros.append(pessoa_id)

        expressao_unidades = (
            "ps.quantidade" if _tem_coluna_quantidade_servico(conexao) else "1"
        )

        resultado = pd.read_sql_query(
            f"""
            SELECT
                pe.id AS pessoa_id,
                pe.nome AS pessoa,

                COUNT(p.id) AS presencas,

                MIN(p.data) AS primeira_no_periodo,

                MAX(p.data) AS ultima_no_periodo,

                COALESCE(
                    SUM((
                        SELECT COUNT(*)
                        FROM presenca_servicos ps
                        WHERE ps.presenca_id = p.id
                    )),
                    0
                ) AS servicos,

                COALESCE(
                    SUM((
                        SELECT COALESCE(
                            SUM({expressao_unidades}),
                            0
                        )
                        FROM presenca_servicos ps
                        WHERE ps.presenca_id = p.id
                    )),
                    0
                ) AS unidades

            FROM pessoas pe

            JOIN presencas p
                ON p.pessoa_id = pe.id

            WHERE p.data BETWEEN ? AND ?
            {filtro}

            GROUP BY pe.id, pe.nome

            ORDER BY presencas DESC, pe.nome
            """,
            conexao,
            params=parametros,
        )

    return resultado


def evolucao_diaria(inicio, fim, pessoa_id=None, ator_id=None):
    """
    Retorna a quantidade de presenças por dia.

    Relatórios gerais: superadmin, admin e consulta.
    Filtro por pessoa: somente superadmin e admin.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_gerais",
        )

        if pessoa_id is not None:
            exigir_permissao_usuario(
                conexao,
                ator_id,
                "relatorios_pessoais",
            )

            if type(pessoa_id) is not int or pessoa_id <= 0:
                raise ValueError("Identificador da pessoa inválido.")

        try:
            if not isinstance(inicio, str) or not isinstance(fim, str):
                raise ValueError()

            data_inicio = date.fromisoformat(inicio)
            data_fim = date.fromisoformat(fim)

            if inicio != data_inicio.isoformat() or fim != data_fim.isoformat():
                raise ValueError()

        except ValueError:
            raise ValueError("Período do relatório inválido.") from None

        if data_inicio > data_fim:
            raise ValueError("A data inicial não pode superar a final.")

        parametros = [inicio, fim]
        filtro = ""

        if pessoa_id is not None:
            filtro = "AND pessoa_id = ?"
            parametros.append(pessoa_id)

        resultado = pd.read_sql_query(
            f"""
            SELECT
                data,
                COUNT(*) AS presencas
            FROM presencas
            WHERE data BETWEEN ? AND ?
            {filtro}
            GROUP BY data
            ORDER BY data
            """,
            conexao,
            params=parametros,
        )

    return resultado


def evolucao_mensal(inicio, fim, pessoa_id=None, ator_id=None):
    """
    Retorna a evolução mensal dos atendimentos.

    Relatórios gerais: superadmin, admin e consulta.
    Filtro por pessoa: somente superadmin e admin.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_gerais",
        )

        if pessoa_id is not None:
            exigir_permissao_usuario(
                conexao,
                ator_id,
                "relatorios_pessoais",
            )

            if type(pessoa_id) is not int or pessoa_id <= 0:
                raise ValueError("Identificador da pessoa inválido.")

        # Validação do período.
        try:
            if not isinstance(inicio, str) or not isinstance(fim, str):
                raise ValueError()

            data_inicio = date.fromisoformat(inicio)
            data_fim = date.fromisoformat(fim)

            if inicio != data_inicio.isoformat() or fim != data_fim.isoformat():
                raise ValueError()

        except ValueError:
            raise ValueError("Período do relatório inválido.") from None

        if data_inicio > data_fim:
            raise ValueError("A data inicial não pode superar a final.")

        parametros = [inicio, fim]
        filtro = ""

        if pessoa_id is not None:
            filtro = "AND pessoa_id = ?"
            parametros.append(pessoa_id)

        resultado = pd.read_sql_query(
            f"""
            SELECT
                SUBSTR(data, 1, 7) AS mes,
                COUNT(*) AS presencas,
                COUNT(DISTINCT pessoa_id) AS pessoas_distintas
            FROM presencas
            WHERE data BETWEEN ? AND ?
            {filtro}
            GROUP BY SUBSTR(data, 1, 7)
            ORDER BY mes
            """,
            conexao,
            params=parametros,
        )

    return resultado


def pessoas_ausentes(data_referencia, dias=30, ator_id=None):
    """
    Retorna pessoas ativas sem atendimento recente.

    Inclui pessoas que nunca compareceram.
    Acesso exclusivo a superadmin e admin.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_pessoais",
        )

        # Valida a data de referência.
        try:
            if not isinstance(data_referencia, str):
                raise ValueError()

            data_validada = date.fromisoformat(data_referencia)

            if data_referencia != data_validada.isoformat():
                raise ValueError()

        except ValueError:
            raise ValueError("Data de referência inválida.") from None

        # Mantém os limites utilizados na interface.
        if type(dias) is not int or not 1 <= dias <= 3650:
            raise ValueError("O número de dias deve ser um inteiro " "entre 1 e 3650.")

        resultado = pd.read_sql_query(
            """
            SELECT
                pe.id,
                pe.nome,
                MAX(p.data) AS ultima_presenca,
                CASE
                    WHEN MAX(p.data) IS NULL THEN NULL
                    ELSE CAST(
                        JULIANDAY(?) - JULIANDAY(MAX(p.data))
                        AS INTEGER
                    )
                END AS dias_sem_comparecer
            FROM pessoas pe
            LEFT JOIN presencas p
                ON p.pessoa_id = pe.id
                AND p.data <= ?
            WHERE pe.ativo = 1
            GROUP BY pe.id, pe.nome
            HAVING MAX(p.data) IS NULL
                OR JULIANDAY(?) - JULIANDAY(MAX(p.data)) >= ?
            ORDER BY
                ultima_presenca IS NOT NULL,
                ultima_presenca,
                pe.nome
            """,
            conexao,
            params=(
                data_referencia,
                data_referencia,
                data_referencia,
                dias,
            ),
        )

    return resultado


def qualidade_cadastros(ator_id=None):
    """
    Consulta a qualidade dos cadastros de pessoas ativas.

    Informa a existência de documento, telefone
    e fotografia, sem retornar seus conteúdos.

    Acesso exclusivo a superadmin e admin.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_pessoais",
        )

        resultado = pd.read_sql_query(
            """
            SELECT
                pe.id,
                pe.nome,
                CASE
                    WHEN pe.documento IS NULL
                      OR TRIM(pe.documento) = ''
                    THEN 'Não'
                    ELSE 'Sim'
                END AS documento,
                CASE
                    WHEN pe.telefone IS NULL
                      OR TRIM(pe.telefone) = ''
                    THEN 'Não'
                    ELSE 'Sim'
                END AS telefone,
                CASE
                    WHEN fp.pessoa_id IS NULL
                    THEN 'Não'
                    ELSE 'Sim'
                END AS fotografia
            FROM pessoas pe
            LEFT JOIN fotos_pessoas fp
                ON fp.pessoa_id = pe.id
            WHERE pe.ativo = 1
            ORDER BY pe.nome
            """,
            conexao,
        )

    return resultado


def indicadores(inicio, fim, pessoa_id=None, ator_id=None):
    """
    Calcula indicadores de atendimento.

    Relatórios gerais:
        superadmin, admin e consulta.

    Indicadores filtrados por pessoa:
        somente superadmin e admin.

    Compatível com SQLite V1, V2 e V3.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_gerais",
        )

        if pessoa_id is not None:
            exigir_permissao_usuario(
                conexao,
                ator_id,
                "relatorios_pessoais",
            )

            if type(pessoa_id) is not int or pessoa_id <= 0:
                raise ValueError("Identificador da pessoa inválido.")

        # Validação do período.
        try:
            if not isinstance(inicio, str) or not isinstance(fim, str):
                raise ValueError()

            data_inicio = date.fromisoformat(inicio)
            data_fim = date.fromisoformat(fim)

            if inicio != data_inicio.isoformat() or fim != data_fim.isoformat():
                raise ValueError()

        except ValueError:
            raise ValueError("Período do relatório inválido.") from None

        if data_inicio > data_fim:
            raise ValueError("A data inicial não pode superar a final.")

        parametros = [inicio, fim]
        filtro = ""

        if pessoa_id is not None:
            filtro = "AND p.pessoa_id = ?"
            parametros.append(pessoa_id)

        # V1/V2: cada vínculo equivale a uma unidade.
        # V3: utiliza a quantidade efetivamente registrada.
        expressao_unidades = (
            "ps.quantidade" if _tem_coluna_quantidade_servico(conexao) else "1"
        )

        resultado = conexao.execute(
            f"""
            SELECT
                COUNT(DISTINCT p.pessoa_id) AS pessoas,

                COUNT(*) AS presencas,

                COALESCE(SUM((
                    SELECT COUNT(*)
                    FROM presenca_servicos ps
                    WHERE ps.presenca_id = p.id
                )), 0) AS servicos,

                COALESCE(SUM((
                    SELECT COALESCE(
                        SUM({expressao_unidades}),
                        0
                    )
                    FROM presenca_servicos ps
                    WHERE ps.presenca_id = p.id
                )), 0) AS unidades,

                COUNT(DISTINCT p.data) AS dias_registrados

            FROM presencas p
            WHERE p.data BETWEEN ? AND ?
            {filtro}
            """,
            parametros,
        ).fetchone()

    pessoas = int(resultado["pessoas"])
    presencas = int(resultado["presencas"])
    servicos = int(resultado["servicos"])
    unidades = int(resultado["unidades"])
    dias = int(resultado["dias_registrados"])

    return {
        "pessoas": pessoas,
        "presencas": presencas,
        "servicos": servicos,
        "unidades": unidades,
        "dias_registrados": dias,
        "media_por_dia": (presencas / dias if dias else 0.0),
    }
