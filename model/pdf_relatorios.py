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

from conn.database import conectar
from model.permissoes import exigir_permissao_usuario
from common.common import BASIC_TITTLE, ANO, VERSAO


def gerar_pdf(titulo, inicio, fim, indicadores, tabelas, ator_id):
    """
    Gera um relatório PDF para usuário autorizado.

    tabelas: lista de tuplas (titulo_secao, DataFrame).
    Retorna bytes de um PDF.
    """

    # Verifica a autorização antes de preparar o PDF.
    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "exportar_relatorios",
        )

    # A partir daqui, permanece o código original.
    COR_PRINCIPAL = colors.HexColor("#444444")
    COR_SECUNDARIA = colors.HexColor("#666666")
    COR_LINHA = colors.HexColor("#DDDDDD")
    COR_ALTERNADA = colors.HexColor("#F5F5F5")

    buffer = BytesIO()

    # Mantenha todo o restante da função original.

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
            name="CelulaPrestServ",
            parent=estilos["Normal"],
            fontSize=8,
            leading=10,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="CabecalhoPrestServ",
            parent=estilos["CelulaPrestServ"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
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
        ["Serviços registrados", str(indicadores["servicos"])],
        ["Unidades distribuídas", str(indicadores["unidades"])],
        ["Dias com registros", str(indicadores["dias_registrados"])],
        [
            "Média por dia com registros",
            f"{indicadores['media_por_dia']:.2f}",
        ],
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
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_ALTERNADA]),
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


def gerar_pdf_entradas(
    registros, ator_id, inicio=None, fim=None, tipo=None, categoria=None
):
    """Gera o relatório PDF das entradas filtradas."""

    with conectar() as conexao:
        exigir_permissao_usuario(conexao, ator_id, "gerenciar_entradas")

    registros = list(registros)
    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=28,
        rightMargin=28,
        topMargin=35,
        bottomMargin=38,
    )

    estilos = getSampleStyleSheet()

    estilos.add(
        ParagraphStyle(
            name="TituloEntradas",
            parent=estilos["Heading1"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#444444"),
            spaceAfter=10,
        )
    )

    estilos.add(
        ParagraphStyle(
            name="CelulaEntradas",
            parent=estilos["Normal"],
            fontSize=7,
            leading=9,
        )
    )

    estilos.add(
        ParagraphStyle(
            name="CabecalhoEntradas",
            parent=estilos["CelulaEntradas"],
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )
    )

    def data_br(valor):
        if valor is None:
            return "Todas"
        if hasattr(valor, "strftime"):
            return valor.strftime("%d/%m/%Y")
        return datetime.strptime(valor, "%Y-%m-%d").strftime("%d/%m/%Y")

    def dinheiro(centavos):
        if centavos is None:
            return "Não informado"

        reais = f"{centavos // 100:,}".replace(",", ".")
        return f"R$ {reais},{centavos % 100:02d}"

    def celula(valor, estilo):
        texto = "" if valor is None else str(valor)
        return Paragraph(escape(texto), estilo)

    tipos = {
        None: "Todos",
        "doacao": "Doações",
        "compra": "Compras",
    }

    periodo = (
        "Todo o histórico"
        if inicio is None and fim is None
        else f"{data_br(inicio)} a {data_br(fim)}"
    )

    filtros = (
        f"Período: {periodo} | "
        f"Tipo: {tipos.get(tipo, tipo)} | "
        f"Categoria: {categoria or 'Todas'}"
    )

    total_doacoes = sum(r["tipo"] == "doacao" for r in registros)
    total_compras = sum(r["tipo"] == "compra" for r in registros)

    valores_compras = [
        r["valor_centavos"]
        for r in registros
        if r["tipo"] == "compra" and r["valor_centavos"] is not None
    ]

    total_informado = (
        dinheiro(sum(valores_compras)) if valores_compras else "Não informado"
    )

    resumo = (
        f"Entradas: {len(registros)} | "
        f"Doações: {total_doacoes} | "
        f"Compras: {total_compras} | "
        f"Valor informado em compras: {total_informado}"
    )

    conteudo = [
        Paragraph(
            escape(BASIC_TITTLE),
            estilos["TituloEntradas"],
        ),
        Paragraph(
            "Relatório de entradas — Doações e Compras",
            estilos["Heading2"],
        ),
        Paragraph(escape(filtros), estilos["Normal"]),
        Spacer(1, 5),
        Paragraph(escape(resumo), estilos["Normal"]),
        Spacer(1, 12),
    ]

    cabecalho = [
        "ID",
        "Data",
        "Tipo",
        "Categoria",
        "Item",
        "Qtd.",
        "Unid.",
        "Origem",
        "Valor total",
        "Registrado por",
    ]

    dados = [[celula(c, estilos["CabecalhoEntradas"]) for c in cabecalho]]

    for r in registros:
        valores = [
            r["id"],
            data_br(r["data"]),
            "Doação" if r["tipo"] == "doacao" else "Compra",
            r["categoria"],
            r["item"],
            str(r["quantidade"]).replace(".", ","),
            r["unidade"],
            r["origem"] or "",
            dinheiro(r["valor_centavos"]),
            r["registrado_por"],
        ]

        dados.append([celula(v, estilos["CelulaEntradas"]) for v in valores])

    pesos = [35, 60, 49, 78, 118, 44, 43, 100, 79, 102]
    fator = (landscape(A4)[0] - 56) / sum(pesos)

    tabela = Table(
        dados,
        colWidths=[p * fator for p in pesos],
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
                    colors.HexColor("#444444"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F5F5F5")],
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.lightgrey,
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    conteudo.append(tabela)

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))

        largura = landscape(A4)[0]

        agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

        canvas.drawString(
            28,
            20,
            f"PrestServ {VERSAO} | " f"Desenvolvido por Jeronimo Costa Penha - {ANO}",
        )

        canvas.drawCentredString(
            largura / 2,
            20,
            f"Emitido em {agora}",
        )

        canvas.drawRightString(
            largura - 28,
            20,
            f"Página {doc.page}",
        )

        canvas.restoreState()

    documento.build(
        conteudo,
        onFirstPage=rodape,
        onLaterPages=rodape,
    )

    return buffer.getvalue()
