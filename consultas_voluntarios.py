"""Consultas e indicadores de voluntariado."""

from datetime import date

from database import conectar
from permissoes import exigir_permissao_usuario


def _validar_periodo(inicio, fim):
    """Valida um período informado em formato ISO."""

    try:
        if not isinstance(inicio, str):
            raise ValueError()

        if not isinstance(fim, str):
            raise ValueError()

        data_inicio = date.fromisoformat(inicio)
        data_fim = date.fromisoformat(fim)

        if inicio != data_inicio.isoformat():
            raise ValueError()

        if fim != data_fim.isoformat():
            raise ValueError()

    except ValueError:
        raise ValueError("Período inválido.") from None

    if data_inicio > data_fim:
        raise ValueError("A data inicial não pode ser posterior à final.")

    return inicio, fim


def ranking_voluntarios(inicio, fim, *, ator_id):
    """
    Ranking por quantidade de dias de presença.

    Empates recebem a mesma colocação.
    Inclui voluntários atualmente inativos.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_voluntarios",
        )

        inicio, fim = _validar_periodo(inicio, fim)

        registros = conexao.execute(
            """
            SELECT
                v.id AS voluntario_id,
                v.nome,
                v.ativo,
                COUNT(p.id) AS presencas
            FROM voluntarios AS v
            JOIN presencas_voluntarios AS p
              ON p.voluntario_id = v.id
            WHERE p.data BETWEEN ? AND ?
            GROUP BY v.id, v.nome, v.ativo
            ORDER BY
                presencas DESC,
                v.nome COLLATE NOCASE,
                v.id
            """,
            (inicio, fim),
        ).fetchall()

    resultado = []
    colocacao = 0
    quantidade_anterior = None

    for registro in registros:
        quantidade = registro["presencas"]

        if quantidade != quantidade_anterior:
            colocacao += 1
            quantidade_anterior = quantidade

        resultado.append(
            {
                "posicao": colocacao,
                "voluntario_id": registro["voluntario_id"],
                "nome": registro["nome"],
                "ativo": bool(registro["ativo"]),
                "presencas": quantidade,
            }
        )

    return resultado


def estatisticas_voluntarios(inicio, fim, *, ator_id):
    """
    Retorna somente indicadores agregados.

    Não expõe nomes, telefones ou identificadores
    individuais de voluntários.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "estatisticas_voluntarios",
        )

        inicio, fim = _validar_periodo(inicio, fim)

        cadastros = conexao.execute("""
            SELECT
                COUNT(*) AS cadastrados,
                COALESCE(SUM(ativo), 0) AS ativos
            FROM voluntarios
            """).fetchone()

        participacao = conexao.execute(
            """
            SELECT
                COUNT(*) AS presencas,
                COUNT(DISTINCT voluntario_id)
                    AS participantes
            FROM presencas_voluntarios
            WHERE data BETWEEN ? AND ?
            """,
            (inicio, fim),
        ).fetchone()

        return {
            "cadastrados": cadastros["cadastrados"],
            "ativos": cadastros["ativos"],
            "inativos": (cadastros["cadastrados"] - cadastros["ativos"]),
            "participantes": participacao["participantes"],
            "presencas": participacao["presencas"],
        }


def destaques_voluntarios(inicio, fim, *, ator_id):
    """
    Seleciona todos os voluntários nas três primeiras
    colocações distintas do ranking.

    Empates são preservados integralmente.
    """

    ranking = ranking_voluntarios(
        inicio,
        fim,
        ator_id=ator_id,
    )

    return [voluntario for voluntario in ranking if voluntario["posicao"] <= 3]


def relatorio_cadastros_voluntarios(inicio, fim, *, ator_id):
    """
    Relação de todos os voluntários cadastrados.

    Inclui ativos, inativos e voluntários sem presenças.

    - presencas_periodo: participações no intervalo
    - presencas_total: participações em todo o histórico
    - ultima_participacao: última presença de toda a história
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_voluntarios",
        )

        inicio, fim = _validar_periodo(inicio, fim)

        registros = conexao.execute(
            """
            SELECT
                v.id AS voluntario_id,
                v.nome,
                v.telefone,
                v.ativo,
                v.criado_em,

                COALESCE(
                    SUM(
                        CASE
                            WHEN p.data BETWEEN ? AND ?
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS presencas_periodo,

                COUNT(p.id) AS presencas_total,

                MAX(p.data) AS ultima_participacao

            FROM voluntarios AS v

            LEFT JOIN presencas_voluntarios AS p
                ON p.voluntario_id = v.id

            GROUP BY
                v.id,
                v.nome,
                v.telefone,
                v.ativo,
                v.criado_em

            ORDER BY
                v.nome COLLATE NOCASE,
                v.id
            """,
            (inicio, fim),
        ).fetchall()

        return [
            {
                **dict(registro),
                "ativo": bool(registro["ativo"]),
            }
            for registro in registros
        ]


def historico_presencas_voluntario(voluntario_id, inicio, fim, *, ator_id):
    """
    Histórico individual de presenças no período.

    Inclui presenças de voluntários inativos.
    """

    if type(voluntario_id) is not int or voluntario_id <= 0:
        raise ValueError("Identificador de voluntário inválido.")

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_voluntarios",
        )

        inicio, fim = _validar_periodo(inicio, fim)

        voluntario = conexao.execute(
            """
            SELECT id
            FROM voluntarios
            WHERE id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        if voluntario is None:
            raise ValueError("Voluntário não encontrado.")

        registros = conexao.execute(
            """
            SELECT
                p.id AS presenca_id,
                p.data,
                p.criado_em,
                u.login AS registrado_por

            FROM presencas_voluntarios AS p

            JOIN usuarios AS u
                ON u.id = p.usuario_id

            WHERE p.voluntario_id = ?
              AND p.data BETWEEN ? AND ?

            ORDER BY
                p.data DESC,
                p.id DESC
            """,
            (voluntario_id, inicio, fim),
        ).fetchall()

        return [dict(registro) for registro in registros]
