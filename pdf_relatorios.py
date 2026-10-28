from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape

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
    KeepTogether,
)

from common import BASIC_TITTLE, ANO, VERSAO


def gerar_pdf(titulo, inicio, fim, indicadores, tabelas):
    """
    tabelas: lista de tuplas (titulo_secao, DataFrame).
    Retorna bytes de um PDF.
    """
    COR_PRINCIPAL = colors.HexColor("#444444")
    COR_SECUNDARIA = colors.HexColor("#666666")
    COR_LINHA = colors.HexColor("#DDDDDD")
    COR_ALTERNADA = colors.HexColor("#F5F5F5")

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=40,
        bottomMargin=40,
    )

    estilos = getSampleStyleSheet()
    estilos.add(
        ParagraphStyle(
            name="TituloPrestServ",
            parent=estilos["Heading1"],
            alignment=TA_CENTER,
            textColor=COR_PRINCIPAL,
            spaceAfter=12,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="CelulaPrestServ", parent=estilos["Normal"], fontSize=7, leading=9
        )
    )
    estilos.add(
        ParagraphStyle(
            name="CabecalhoPrestServ",
            parent=estilos["CelulaPrestServ"],
            textColor=colors.white,
            fontName="Helvetica-Bold",
        )
    )

    conteudo = [
        Paragraph(BASIC_TITTLE, estilos["TituloPrestServ"]),
        Paragraph(escape(titulo), estilos["Heading2"]),
        Paragraph(
            f"Período: {inicio.strftime('%d/%m/%Y')} " f"a {fim.strftime('%d/%m/%Y')}",
            estilos["Normal"],
        ),
        Spacer(1, 12),
    ]

    resumo = [
        ["Indicador", "Quantidade"],
        ["Pessoas distintas", str(indicadores["pessoas"])],
        ["Presenças", str(indicadores["presencas"])],
        ["Serviços prestados", str(indicadores["servicos"])],
        ["Dias com registros", str(indicadores["dias_registrados"])],
        ["Média por dia com registros", f"{indicadores['media_por_dia']:.2f}"],
    ]

    tabela_resumo = Table(resumo, colWidths=[210, 110], hAlign="LEFT")
    tabela_resumo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COR_PRINCIPAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    conteudo.extend([tabela_resumo, Spacer(1, 20)])

    for titulo_secao, df in tabelas:
        if df.empty:
            continue

        conteudo.append(Paragraph(escape(titulo_secao), estilos["Heading2"]))
        conteudo.append(Spacer(1, 8))

        colunas = list(df.columns)

        # Distribui a largura disponível entre as colunas.
        largura = landscape(A4)[0] - 60
        largura_coluna = largura / len(colunas)

        dados = [
            [
                Paragraph(
                    escape(str(col).replace("_", " ").title()),
                    estilos["CabecalhoPrestServ"],
                )
                for col in colunas
            ]
        ]

        for linha in df.itertuples(index=False, name=None):
            dados.append(
                [
                    Paragraph(
                        escape("" if valor is None else str(valor)),
                        estilos["CelulaPrestServ"],
                    )
                    for valor in linha
                ]
            )

        tabela = Table(
            dados,
            colWidths=[largura_coluna] * len(colunas),
            repeatRows=1,
            hAlign="LEFT",
        )

        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COR_PRINCIPAL),
                    ("TEXTCOLOR", (0, 0), (-1, 0), COR_PRINCIPAL),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F0F3F7")],
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        conteudo.extend([tabela, Spacer(1, 20)])

    def rodape(canvas, doc):
        canvas.saveState()

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COR_SECUNDARIA)

        agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

        largura = landscape(A4)[0]

        canvas.drawString(
            30,
            22,
            f"PrestServ {VERSAO} | Desenvolvido por Jeronimo Costa Penha - {ANO}",
        )

        canvas.drawCentredString(largura / 2, 22, f"Emitido em {agora}")

        canvas.drawRightString(largura - 30, 22, f"Página {doc.page}")

        canvas.restoreState()

    documento.build(conteudo, onFirstPage=rodape, onLaterPages=rodape)

    return buffer.getvalue()
