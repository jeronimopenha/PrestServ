"""Geração de relatórios PDF de voluntários."""

from datetime import date, datetime
from io import BytesIO
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from common import BASIC_TITTLE, VERSAO, ANO
from database import conectar
from permissoes import exigir_permissao_usuario
from consultas_voluntarios import (
    ranking_voluntarios,
    relatorio_cadastros_voluntarios,
    historico_presencas_voluntario,
)


def gerar_pdf_ranking_voluntarios(inicio, fim, *, ator_id):
    """Gera o PDF do ranking de voluntários por período."""

    # A autorização para exportar é independente
    # da autorização para consultar o ranking.
    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "exportar_relatorios_voluntarios",
        )

    # Esta consulta também valida o período e
    # verifica as permissões do operador.
    ranking = ranking_voluntarios(
        inicio,
        fim,
        ator_id=ator_id,
    )

    data_inicio = date.fromisoformat(inicio)
    data_fim = date.fromisoformat(fim)

    cor_principal = colors.HexColor("#444444")
    cor_secundaria = colors.HexColor("#666666")
    cor_alternada = colors.HexColor("#F5F5F5")

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=43,
        title="PrestServ - Ranking de voluntários",
        author="Jeronimo Costa Penha",
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloRankingVoluntarios",
        parent=estilos["Heading1"],
        alignment=TA_CENTER,
        textColor=cor_principal,
        spaceAfter=12,
    )

    celula = ParagraphStyle(
        "CelulaRankingVoluntarios",
        parent=estilos["Normal"],
        fontSize=9,
        leading=12,
    )

    conteudo = [
        Paragraph(
            escape(BASIC_TITTLE),
            titulo,
        ),
        Paragraph(
            "Ranking de participação dos voluntários",
            estilos["Heading2"],
        ),
        Paragraph(
            f"Período: {data_inicio:%d/%m/%Y} " f"a {data_fim:%d/%m/%Y}",
            estilos["Normal"],
        ),
        Spacer(1, 12),
        Paragraph(
            f"Participantes: {len(ranking)}"
            f" | Presenças registradas: "
            f"{sum(r['presencas'] for r in ranking)}",
            estilos["Normal"],
        ),
        Spacer(1, 12),
    ]

    if ranking:
        largura = landscape(A4)[0] - 72

        dados = [
            [
                "Posição",
                "Voluntário",
                "Presenças",
                "Situação",
            ]
        ]

        for registro in ranking:
            dados.append(
                [
                    f"{registro['posicao']}º",
                    Paragraph(
                        escape(str(registro["nome"])),
                        celula,
                    ),
                    str(registro["presencas"]),
                    ("Ativo" if registro["ativo"] else "Inativo"),
                ]
            )

        tabela = Table(
            dados,
            colWidths=[
                62,
                largura - 62 - 96 - 118,
                96,
                118,
            ],
            repeatRows=1,
            hAlign="LEFT",
        )

        tabela.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        cor_principal,
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, cor_alternada],
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.25,
                        colors.lightgrey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (0, -1),
                        "CENTER",
                    ),
                    (
                        "ALIGN",
                        (2, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        conteudo.append(tabela)

        total_destaques = sum(registro["posicao"] <= 3 for registro in ranking)

        conteudo.extend(
            [
                Spacer(1, 14),
                Paragraph(
                    f"Voluntários nas três primeiras "
                    f"colocações: {total_destaques}. "
                    "Empates compartilham a mesma posição.",
                    estilos["Normal"],
                ),
            ]
        )

    else:
        conteudo.append(
            Paragraph(
                "Nenhuma participação registrada " "no período selecionado.",
                estilos["Normal"],
            )
        )

    def rodape(canvas, doc):
        canvas.saveState()

        largura_pagina = landscape(A4)[0]

        agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(cor_secundaria)

        canvas.drawString(
            36,
            22,
            f"PrestServ {VERSAO} | " f"Desenvolvido por Jeronimo Costa Penha - {ANO}",
        )

        canvas.drawCentredString(
            largura_pagina / 2,
            22,
            f"Emitido em {agora}",
        )

        canvas.drawRightString(
            largura_pagina - 36,
            22,
            f"Página {doc.page}",
        )

        canvas.restoreState()

    documento.build(
        conteudo,
        onFirstPage=rodape,
        onLaterPages=rodape,
    )

    return buffer.getvalue()


def gerar_pdf_cadastros_voluntarios(inicio, fim, *, ator_id):
    """Gera a relação PDF de voluntários cadastrados."""

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "exportar_relatorios_voluntarios",
        )

    registros = relatorio_cadastros_voluntarios(inicio, fim, ator_id=ator_id)

    data_inicio = date.fromisoformat(inicio)
    data_fim = date.fromisoformat(fim)

    cor_principal = colors.HexColor("#444444")
    cor_secundaria = colors.HexColor("#666666")
    cor_alternada = colors.HexColor("#F5F5F5")

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=43,
        title="PrestServ - Voluntários cadastrados",
        author="Jeronimo Costa Penha",
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloCadastrosVoluntarios",
        parent=estilos["Heading1"],
        alignment=TA_CENTER,
        textColor=cor_principal,
        spaceAfter=12,
    )

    celula = ParagraphStyle(
        "CelulaCadastrosVoluntarios",
        parent=estilos["Normal"],
        fontSize=7.5,
        leading=10,
        splitLongWords=1,
    )

    cabecalho = ParagraphStyle(
        "CabecalhoCadastrosVoluntarios",
        parent=celula,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    total_ativos = sum(r["ativo"] for r in registros)
    total_presencas = sum(r["presencas_periodo"] for r in registros)

    conteudo = [
        Paragraph(escape(BASIC_TITTLE), titulo),
        Paragraph(
            "Relação de voluntários cadastrados",
            estilos["Heading2"],
        ),
        Paragraph(
            f"Período: {data_inicio:%d/%m/%Y} " f"a {data_fim:%d/%m/%Y}",
            estilos["Normal"],
        ),
        Spacer(1, 12),
        Paragraph(
            f"Cadastrados: {len(registros)} | "
            f"Ativos: {total_ativos} | "
            f"Inativos: {len(registros) - total_ativos} | "
            f"Presenças no período: {total_presencas}",
            estilos["Normal"],
        ),
        Spacer(1, 14),
    ]

    if registros:
        colunas = [
            "ID",
            "Voluntário",
            "Telefone",
            "Situação",
            "Cadastro",
            "No período",
            "Total",
            "Última presença",
        ]

        dados = [[Paragraph(escape(coluna), cabecalho) for coluna in colunas]]

        for r in registros:
            cadastro = date.fromisoformat(r["criado_em"][:10]).strftime("%d/%m/%Y")

            ultima = (
                date.fromisoformat(r["ultima_participacao"]).strftime("%d/%m/%Y")
                if r["ultima_participacao"]
                else "Nunca"
            )

            valores = [
                r["voluntario_id"],
                r["nome"],
                r["telefone"] or "-",
                "Ativo" if r["ativo"] else "Inativo",
                cadastro,
                r["presencas_periodo"],
                r["presencas_total"],
                ultima,
            ]

            dados.append(
                [
                    Paragraph(
                        escape(str(valor)),
                        celula,
                    )
                    for valor in valores
                ]
            )

        largura = landscape(A4)[0] - 72

        tabela = Table(
            dados,
            colWidths=[
                35,
                218,
                100,
                68,
                82,
                80,
                65,
                largura - 648,
            ],
            repeatRows=1,
            hAlign="LEFT",
        )

        tabela.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        cor_principal,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, cor_alternada],
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.25,
                        colors.lightgrey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        conteudo.append(tabela)

    else:
        conteudo.append(
            Paragraph(
                "Nenhum voluntário cadastrado.",
                estilos["Normal"],
            )
        )

    conteudo.extend(
        [
            Spacer(1, 14),
            Paragraph(
                "As presenças do período consideram "
                "somente o intervalo selecionado. "
                "O total e a última participação "
                "consideram todo o histórico.",
                estilos["Normal"],
            ),
        ]
    )

    def rodape(canvas, doc):
        canvas.saveState()

        largura_pagina = landscape(A4)[0]

        agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(cor_secundaria)

        canvas.drawString(
            36,
            22,
            f"PrestServ {VERSAO} | " f"Desenvolvido por Jeronimo Costa Penha - {ANO}",
        )

        canvas.drawCentredString(
            largura_pagina / 2,
            22,
            f"Emitido em {agora}",
        )

        canvas.drawRightString(
            largura_pagina - 36,
            22,
            f"Página {doc.page}",
        )

        canvas.restoreState()

    documento.build(
        conteudo,
        onFirstPage=rodape,
        onLaterPages=rodape,
    )

    return buffer.getvalue()


def gerar_pdf_historico_voluntario(voluntario_id, inicio, fim, *, ator_id):
    """Gera o PDF do histórico individual de um voluntário."""

    if type(voluntario_id) is not int or voluntario_id <= 0:
        raise ValueError("Identificador de voluntário inválido.")

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "exportar_relatorios_voluntarios",
        )

        voluntario = conexao.execute(
            """
            SELECT id, nome, ativo
            FROM voluntarios
            WHERE id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        if voluntario is None:
            raise ValueError("Voluntário não encontrado.")

        nome = voluntario["nome"]
        ativo = bool(voluntario["ativo"])

    historico = historico_presencas_voluntario(
        voluntario_id,
        inicio,
        fim,
        ator_id=ator_id,
    )

    data_inicio = date.fromisoformat(inicio)
    data_fim = date.fromisoformat(fim)

    cor_principal = colors.HexColor("#444444")
    cor_secundaria = colors.HexColor("#666666")
    cor_alternada = colors.HexColor("#F5F5F5")

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=43,
        title="PrestServ - Histórico de voluntário",
        author="Jeronimo Costa Penha",
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloHistoricoVoluntario",
        parent=estilos["Heading1"],
        alignment=TA_CENTER,
        textColor=cor_principal,
        spaceAfter=12,
    )

    celula = ParagraphStyle(
        "CelulaHistoricoVoluntario",
        parent=estilos["Normal"],
        fontSize=9,
        leading=12,
        splitLongWords=1,
    )

    cabecalho = ParagraphStyle(
        "CabecalhoHistoricoVoluntario",
        parent=celula,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    conteudo = [
        Paragraph(
            escape(BASIC_TITTLE),
            titulo,
        ),
        Paragraph(
            "Histórico individual de participação",
            estilos["Heading2"],
        ),
        Spacer(1, 8),
        Paragraph(
            f"<b>Voluntário:</b> {escape(nome)}",
            estilos["Normal"],
        ),
        Paragraph(
            f"<b>Identificador:</b> {voluntario_id}",
            estilos["Normal"],
        ),
        Paragraph(
            "<b>Situação atual:</b> " + ("Ativo" if ativo else "Inativo"),
            estilos["Normal"],
        ),
        Paragraph(
            f"<b>Período:</b> " f"{data_inicio:%d/%m/%Y} " f"a {data_fim:%d/%m/%Y}",
            estilos["Normal"],
        ),
        Spacer(1, 12),
        Paragraph(
            f"<b>Total de presenças no período:</b> " f"{len(historico)}",
            estilos["Normal"],
        ),
        Spacer(1, 14),
    ]

    if historico:
        dados = [
            [
                Paragraph("Data da presença", cabecalho),
                Paragraph("Registrado em", cabecalho),
                Paragraph("Operador responsável", cabecalho),
            ]
        ]

        for registro in historico:
            data_presenca = date.fromisoformat(registro["data"]).strftime("%d/%m/%Y")

            dados.append(
                [
                    Paragraph(
                        data_presenca,
                        celula,
                    ),
                    Paragraph(
                        escape(str(registro["criado_em"])),
                        celula,
                    ),
                    Paragraph(
                        escape(str(registro["registrado_por"])),
                        celula,
                    ),
                ]
            )

        largura = landscape(A4)[0] - 72

        tabela = Table(
            dados,
            colWidths=[
                150,
                210,
                largura - 360,
            ],
            repeatRows=1,
            hAlign="LEFT",
        )

        tabela.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        cor_principal,
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, cor_alternada],
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.25,
                        colors.lightgrey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        conteudo.append(tabela)

    else:
        conteudo.append(
            Paragraph(
                "O voluntário não possui presenças "
                "registradas no período selecionado.",
                estilos["Normal"],
            )
        )

    conteudo.extend(
        [
            Spacer(1, 16),
            Paragraph(
                "Este documento apresenta os registros "
                "de presença armazenados no PrestServ. "
                "As participações são contabilizadas por dia, "
                "sem atribuição de carga horária.",
                estilos["Normal"],
            ),
        ]
    )

    def rodape(canvas, doc):
        canvas.saveState()

        largura_pagina = landscape(A4)[0]

        agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(cor_secundaria)

        canvas.drawString(
            36,
            22,
            f"PrestServ {VERSAO} | " f"Desenvolvido por Jeronimo Costa Penha - {ANO}",
        )

        canvas.drawCentredString(
            largura_pagina / 2,
            22,
            f"Emitido em {agora}",
        )

        canvas.drawRightString(
            largura_pagina - 36,
            22,
            f"Página {doc.page}",
        )

        canvas.restoreState()

    documento.build(
        conteudo,
        onFirstPage=rodape,
        onLaterPages=rodape,
    )

    return buffer.getvalue()
