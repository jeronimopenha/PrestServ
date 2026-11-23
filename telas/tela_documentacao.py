
"""Consulta e download de manuais autorizados do PrestServ."""

from pathlib import Path

import streamlit as st

from conn.database import conectar


PASTA_DOCS = Path(__file__).resolve().parent.parent / "docs"

# Arquivos permitidos e perfis autorizados.
DOCUMENTOS = {
    "Visão geral": (
        "visao_geral.pdf",
        {"superadmin", "admin", "secretaria", "porteiro", "consulta"},
    ),
    "Manual do porteiro": (
        "manual_porteiro.pdf",
        {"superadmin", "admin", "porteiro"},
    ),
    "Manual da secretaria": (
        "manual_secretaria.pdf",
        {"superadmin", "admin", "secretaria"},
    ),
    "Manual de consulta": (
        "manual_consulta.pdf",
        {"superadmin", "admin", "consulta"},
    ),
    "Manual do administrador": (
        "manual_administrador.pdf",
        {"superadmin", "admin"},
    ),
    "Instalação e manutenção": (
        "instalacao_manutencao.pdf",
        {"superadmin"},
    ),
    "Manual completo": (
        "manual_completo.pdf",
        {"superadmin"},
    ),
}


def tela_documentacao():
    st.subheader("Documentação do PrestServ")

    usuario = st.session_state.get("usuario")

    if not usuario:
        st.error("Faça login para acessar os manuais.")
        return

    # Revalida a conta no banco antes de oferecer documentos.
    with conectar() as conexao:
        registro = conexao.execute(
            """
            SELECT perfil
            FROM usuarios
            WHERE id = ? AND ativo = 1
            """,
            (usuario["id"],),
        ).fetchone()

    if registro is None:
        st.error("Conta inexistente ou inativa.")
        return

    perfil = registro["perfil"]

    opcoes = [
        titulo
        for titulo, (_, perfis) in DOCUMENTOS.items()
        if perfil in perfis
    ]

    if not opcoes:
        st.error("Você não tem permissão para consultar documentos.")
        return

    titulo = st.selectbox("Escolha um documento", opcoes)

    nome_arquivo, perfis_autorizados = DOCUMENTOS[titulo]

    # Verifica a permissão antes de abrir o arquivo.
    if perfil not in perfis_autorizados:
        st.error("Acesso negado.")
        return

    arquivo = PASTA_DOCS / nome_arquivo

    if not arquivo.is_file():
        st.warning("PDF indisponível. Gere os manuais novamente.")
        return

    conteudo = arquivo.read_bytes()

    st.pdf(conteudo, height=650)

    st.download_button(
        "Baixar PDF",
        data=conteudo,
        file_name=nome_arquivo,
        mime="application/pdf",
        on_click="ignore",
        width="stretch",
    )
