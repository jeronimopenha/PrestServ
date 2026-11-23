"""Certificados de reconhecimento dos voluntários."""

from datetime import date, datetime
from io import BytesIO
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from common.common import BASIC_TITTLE, VERSAO
from conn.database import conectar
from model.permissoes import exigir_permissao_usuario
from model.consultas_voluntarios import destaques_voluntarios


def gerar_certificados_voluntarios(inicio, fim, *, ator_id):
    """
    Gera um PDF com um certificado por voluntário.

    Contempla as três primeiras colocações distintas,
    preservando todos os empates.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "gerar_certificados_voluntarios",
        )

    destaques = destaques_voluntarios(
        inicio,
        fim,
        ator_id=ator_id,
    )

    if not destaques:
        raise ValueError(
            "Não há voluntários classificados para "
            "receber certificados neste período."
        )

    data_inicio = date.fromisoformat(inicio)
    data_fim = date.fromisoformat(fim)

    buffer = BytesIO()
    largura, altura = landscape(A4)

    pdf = canvas.Canvas(
        buffer,
        pagesize=landscape(A4),
        pageCompression=1,
    )

    pdf.setTitle("PrestServ - Certificados de reconhecimento")
    pdf.setAuthor("Jeronimo Costa Penha")
    pdf.setSubject("Reconhecimento da participação de voluntários")

    cor_principal = colors.HexColor("#383838")
    cor_secundaria = colors.HexColor("#666666")
    cor_suave = colors.HexColor("#BBBBBB")

    emitido_em = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

    for voluntario in destaques:
        nome = voluntario["nome"]
        posicao = voluntario["posicao"]
        presencas = voluntario["presencas"]

        # Moldura externa.
        pdf.setStrokeColor(cor_principal)
        pdf.setLineWidth(2)
        pdf.roundRect(
            25,
            25,
            largura - 50,
            altura - 50,
            10,
            stroke=1,
            fill=0,
        )

        # Moldura interna.
        pdf.setStrokeColor(cor_suave)
        pdf.setLineWidth(0.7)
        pdf.roundRect(
            34,
            34,
            largura - 68,
            altura - 68,
            7,
            stroke=1,
            fill=0,
        )

        pdf.setFillColor(cor_secundaria)
        pdf.setFont("Helvetica-Bold", 14)

        pdf.drawCentredString(
            largura / 2,
            altura - 81,
            BASIC_TITTLE,
        )

        pdf.setFillColor(cor_principal)
        pdf.setFont("Helvetica-Bold", 25)

        pdf.drawCentredString(
            largura / 2,
            altura - 137,
            "CERTIFICADO DE RECONHECIMENTO",
        )

        pdf.setStrokeColor(cor_suave)
        pdf.line(
            90,
            altura - 153,
            largura - 90,
            altura - 153,
        )

        pdf.setFont("Helvetica", 13)
        pdf.drawCentredString(
            largura / 2,
            altura - 183,
            "Concedemos este certificado a",
        )

        # Nome centralizado, com ajuste de tamanho
        # para acomodar nomes mais compridos.
        for tamanho in (30, 28, 26, 24, 22, 20, 18, 16, 14):
            estilo_nome = ParagraphStyle(
                "NomeCertificado",
                fontName="Helvetica-Bold",
                fontSize=tamanho,
                leading=tamanho + 5,
                alignment=TA_CENTER,
                textColor=cor_principal,
                splitLongWords=1,
            )

            nome_formatado = Paragraph(
                escape(str(nome)),
                estilo_nome,
            )

            _, altura_nome = nome_formatado.wrap(
                largura - 152,
                110,
            )

            if altura_nome <= 90:
                break

        nome_formatado.drawOn(
            pdf,
            76,
            356 - altura_nome / 2,
        )

        # Texto de reconhecimento.
        texto = (
            "Em reconhecimento à participação nas ações "
            "de voluntariado registradas no PrestServ "
            f"durante o período de {data_inicio:%d/%m/%Y} "
            f"a {data_fim:%d/%m/%Y}, alcançando a seguinte "
            "colocação no ranking de presenças:"
        )

        estilo_texto = ParagraphStyle(
            "TextoCertificado",
            fontName="Helvetica",
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            textColor=cor_secundaria,
        )

        paragrafo = Paragraph(
            escape(texto),
            estilo_texto,
        )

        _, altura_texto = paragrafo.wrap(
            largura - 150,
            90,
        )

        paragrafo.drawOn(
            pdf,
            75,
            299 - altura_texto,
        )

        # Colocação.
        pdf.setFillColor(cor_principal)
        pdf.setFont("Helvetica-Bold", 23)

        pdf.drawCentredString(
            largura / 2,
            201,
            f"{posicao}º LUGAR",
        )

        pdf.setFont("Helvetica", 12)

        pdf.drawCentredString(
            largura / 2,
            175,
            f"{presencas} dia(s) de presença registrados",
        )

        pdf.setFont("Helvetica-Oblique", 9)
        pdf.setFillColor(cor_secundaria)

        pdf.drawCentredString(
            largura / 2,
            151,
            "A classificação preserva os empates.",
        )

        # Espaço para assinatura institucional.
        pdf.setStrokeColor(cor_secundaria)

        pdf.line(
            largura / 2 - 145,
            113,
            largura / 2 + 145,
            113,
        )

        pdf.setFont("Helvetica", 10)

        pdf.drawCentredString(
            largura / 2,
            98,
            "Assinatura do responsável pela instituição",
        )

        # Rodapé.
        pdf.setFillColor(cor_secundaria)
        pdf.setFont("Helvetica", 8)

        pdf.drawCentredString(
            largura / 2,
            64,
            f"Emitido em {emitido_em} | PrestServ {VERSAO}",
        )

        pdf.showPage()

    pdf.save()

    return buffer.getvalue()
