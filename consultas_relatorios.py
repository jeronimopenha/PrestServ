import pandas as pd
from database import conectar


def consultar(sql, parametros=()):
    with conectar() as conexao:
        return pd.read_sql_query(sql, conexao, params=parametros)


def presencas_detalhadas(inicio, fim, pessoa_id=None):
    filtro = ""
    params = [inicio, fim]

    if pessoa_id is not None:
        filtro = "AND p.pessoa_id = ?"
        params.append(pessoa_id)

    return consultar(
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
            p.criado_em AS registrado_em
        FROM presencas p
        JOIN pessoas pe ON pe.id = p.pessoa_id
        LEFT JOIN presenca_servicos ps
            ON ps.presenca_id = p.id
        LEFT JOIN servicos s
            ON s.id = ps.servico_id
        WHERE p.data BETWEEN ? AND ?
        {filtro}
        GROUP BY
            p.id, p.data, pe.id, pe.nome, p.criado_em
        ORDER BY p.data DESC, pe.nome
        """,
        params,
    )


def servicos_por_tipo(inicio, fim, pessoa_id=None):
    filtro = ""
    params = [inicio, fim]

    if pessoa_id is not None:
        filtro = "AND p.pessoa_id = ?"
        params.append(pessoa_id)

    return consultar(
        f"""
        SELECT
            s.nome AS servico,
            COUNT(*) AS quantidade
        FROM presenca_servicos ps
        JOIN servicos s ON s.id = ps.servico_id
        JOIN presencas p ON p.id = ps.presenca_id
        WHERE p.data BETWEEN ? AND ?
        {filtro}
        GROUP BY s.id, s.nome
        ORDER BY quantidade DESC, s.nome
        """,
        params,
    )


def frequencia_pessoas(inicio, fim, pessoa_id=None):
    filtro = ""
    params = [inicio, fim]

    if pessoa_id is not None:
        filtro = "AND pe.id = ?"
        params.append(pessoa_id)

    return consultar(
        f"""
        SELECT
            pe.id AS pessoa_id,
            pe.nome AS pessoa,
            COUNT(p.id) AS presencas,
            MIN(p.data) AS primeira_no_periodo,
            MAX(p.data) AS ultima_no_periodo,
            COALESCE(SUM((
                SELECT COUNT(*)
                FROM presenca_servicos ps
                WHERE ps.presenca_id = p.id
            )), 0) AS servicos
        FROM pessoas pe
        JOIN presencas p ON p.pessoa_id = pe.id
        WHERE p.data BETWEEN ? AND ?
        {filtro}
        GROUP BY pe.id, pe.nome
        ORDER BY presencas DESC, pe.nome
        """,
        params,
    )


def evolucao_diaria(inicio, fim, pessoa_id=None):
    filtro = ""
    params = [inicio, fim]

    if pessoa_id is not None:
        filtro = "AND pessoa_id = ?"
        params.append(pessoa_id)

    return consultar(
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
        params,
    )


def evolucao_mensal(inicio, fim, pessoa_id=None):
    filtro = ""
    params = [inicio, fim]

    if pessoa_id is not None:
        filtro = "AND pessoa_id = ?"
        params.append(pessoa_id)

    return consultar(
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
        params,
    )


def pessoas_ausentes(data_referencia, dias=30):
    return consultar(
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
        (data_referencia, data_referencia, data_referencia, dias),
    )


def qualidade_cadastros():
    return consultar("""
        SELECT
            pe.id,
            pe.nome,
            CASE WHEN pe.documento IS NULL
                      OR TRIM(pe.documento) = ''
                 THEN 'Não' ELSE 'Sim' END AS documento,
            CASE WHEN pe.telefone IS NULL
                      OR TRIM(pe.telefone) = ''
                 THEN 'Não' ELSE 'Sim' END AS telefone,
            CASE WHEN fp.pessoa_id IS NULL
                 THEN 'Não' ELSE 'Sim' END AS fotografia
        FROM pessoas pe
        LEFT JOIN fotos_pessoas fp
            ON fp.pessoa_id = pe.id
        WHERE pe.ativo = 1
        ORDER BY pe.nome
        """)


def indicadores(inicio, fim, pessoa_id=None):
    df = presencas_detalhadas(inicio, fim, pessoa_id)

    if df.empty:
        return {
            "pessoas": 0,
            "presencas": 0,
            "servicos": 0,
            "dias_registrados": 0,
            "media_por_dia": 0.0,
        }

    dias = df["data"].nunique()

    return {
        "pessoas": int(df["pessoa_id"].nunique()),
        "presencas": len(df),
        "servicos": int(df["quantidade_servicos"].sum()),
        "dias_registrados": dias,
        "media_por_dia": len(df) / dias,
    }
