from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from backup import gerar_backup, restaurar_backup


def tela_backups():
    st.subheader("Backup e restauração")

    aba_backup, aba_restauracao = st.tabs(["Fazer backup", "Restaurar backup"])

    with aba_backup:
        st.write(
            "Baixe uma cópia completa do banco de dados, "
            "incluindo cadastros, atendimentos, usuários "
            "e fotografias."
        )

        agora = datetime.now(ZoneInfo("America/Sao_Paulo"))

        nome = agora.strftime("prestserv_backup_%Y%m%d_%H%M%S.zip")

        if st.button("Preparar backup"):
            try:
                st.session_state["backup_preparado"] = (nome, gerar_backup())
            except Exception as erro:
                st.error(f"Erro ao preparar backup: {erro}")

        if "backup_preparado" in st.session_state:
            nome_arquivo, conteudo = st.session_state["backup_preparado"]

            st.download_button(
                "Baixar backup ZIP",
                data=conteudo,
                file_name=nome_arquivo,
                mime="application/zip",
                type="primary",
                use_container_width=True,
            )

    with aba_restauracao:
        st.warning(
            "A restauração substituirá todos os dados atuais. "
            "Realize esta operação somente quando não houver "
            "outros usuários utilizando o sistema."
        )

        arquivo = st.file_uploader(
            "Selecione um backup do PrestServ (.zip)",
            type=["zip"],
            key="arquivo_restauracao",
        )

        if arquivo is not None:
            st.write(f"Arquivo: {arquivo.name}")
            st.write(f"Tamanho: {arquivo.size / 1024 / 1024:.2f} MB")

            confirmar = st.checkbox(
                "Confirmo que desejo substituir o banco "
                "atual pelo conteúdo deste arquivo."
            )

            if st.button(
                "Restaurar banco de dados", disabled=not confirmar, type="primary"
            ):
                try:
                    restaurar_backup(arquivo.getvalue())

                    st.session_state.pop("backup_preparado", None)

                    st.session_state.clear()
                    st.rerun()

                except (ValueError, Exception) as erro:
                    st.error(f"Não foi possível restaurar: {erro}")
