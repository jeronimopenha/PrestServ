from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from common.backup import gerar_backup, restaurar_backup
from conn.database import conectar, registrar_log


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
                ator = st.session_state["usuario"]
                conteudo = gerar_backup(ator_id=ator["id"])

                with conectar() as conexao:
                    registrar_log(
                        conexao,
                        acao="gerar_backup",
                        usuario_id=ator["id"],
                        usuario_login=ator["login"],
                        entidade="sistema",
                        detalhes={
                            "arquivo": nome,
                            "tamanho_bytes": len(conteudo),
                        },
                    )

                st.session_state["backup_preparado"] = (
                    nome,
                    conteudo,
                )

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
                width="stretch",
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
                    ator = st.session_state["usuario"]

                    restaurar_backup(
                        arquivo.getvalue(),
                        ator_id=ator["id"],
                        ator_login=ator["login"],
                    )

                    st.session_state.pop("backup_preparado", None)

                    st.session_state.clear()
                    st.rerun()

                except (ValueError, Exception) as erro:
                    st.error(f"Não foi possível restaurar: {erro}")
