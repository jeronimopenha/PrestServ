"""Interface administrativa de cadastro de voluntários."""

import streamlit as st

from conn.database import conectar
from security.permissoes import exigir_permissao_usuario, tem_permissao
from model.voluntarios import (
    cadastrar_voluntario,
    listar_voluntarios,
    buscar_voluntario,
    atualizar_voluntario,
    alterar_situacao_voluntario,
    excluir_voluntario,
    salvar_foto_voluntario,
    buscar_foto_voluntario,
    remover_foto_voluntario,
)


def tela_cadastros_voluntarios():
    ator_id = st.session_state["usuario"]["id"]

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(conexao, ator_id, "cadastrar_voluntarios")

    st.subheader("Cadastro de voluntários")

    aba_novo, aba_editar = st.tabs(
        [
            "Novo voluntário",
            "Consultar / editar",
        ]
    )

    with aba_novo:
        _novo_voluntario(ator_id)

    with aba_editar:
        _editar_voluntario(ator_id, perfil)


def _novo_voluntario(ator_id):
    with st.form("form_novo_voluntario", clear_on_submit=True):
        nome = st.text_input("Nome completo *")
        telefone = st.text_input("Telefone (opcional)")

        foto = st.file_uploader(
            "Fotografia (opcional)",
            type=["jpg", "jpeg", "png", "webp"],
            key="foto_novo_voluntario",
        )

        salvar = st.form_submit_button(
            "Cadastrar voluntário",
            type="primary",
            width="stretch",
        )

    if salvar:
        try:
            voluntario_id = cadastrar_voluntario(nome, telefone, ator_id=ator_id)

        except (ValueError, PermissionError) as erro:
            st.error(str(erro))
            return

        if foto is not None:
            try:
                salvar_foto_voluntario(
                    voluntario_id,
                    foto.getvalue(),
                    ator_id=ator_id,
                )
            except (ValueError, PermissionError) as erro:
                st.warning(
                    f"Voluntário #{voluntario_id} cadastrado, "
                    f"mas a fotografia não foi salva: {erro}"
                )
                return

        st.success(f"Voluntário #{voluntario_id} cadastrado com sucesso!")


def _editar_voluntario(ator_id, perfil):
    voluntarios = listar_voluntarios(ator_id=ator_id)

    if not voluntarios:
        st.info("Nenhum voluntário cadastrado.")
        return

    opcoes = {
        v["id"]: (
            f"{v['nome']} (ID {v['id']})" + (" [Inativo]" if not v["ativo"] else "")
        )
        for v in voluntarios
    }

    voluntario_id = st.selectbox(
        "Selecione o voluntário",
        options=list(opcoes),
        format_func=lambda vid: opcoes[vid],
        index=None,
        placeholder="Digite ou selecione um voluntário...",
        key="cadastro_voluntario_selecionado",
    )

    if voluntario_id is None:
        return

    voluntario = buscar_voluntario(voluntario_id, ator_id=ator_id)

    if voluntario is None:
        st.warning("Voluntário não encontrado.")
        return

    foto_atual = buscar_foto_voluntario(voluntario_id, ator_id=ator_id)

    if foto_atual:
        st.image(foto_atual, width=180)
    else:
        st.caption("Sem fotografia cadastrada.")

    st.caption(f"Identificador: {voluntario_id}")

    if voluntario["ativo"]:
        st.success("Voluntário ativo")
    else:
        st.warning("Voluntário inativo")

    # Dados cadastrais
    with st.form(f"form_editar_voluntario_{voluntario_id}"):
        nome = st.text_input(
            "Nome completo *",
            value=voluntario["nome"],
        )

        telefone = st.text_input(
            "Telefone",
            value=voluntario["telefone"] or "",
        )

        salvar = st.form_submit_button(
            "Salvar alterações",
            type="primary",
            width="stretch",
        )

    if salvar:
        try:
            alterou = atualizar_voluntario(
                voluntario_id,
                nome,
                telefone,
                ator_id=ator_id,
            )
            if alterou:
                st.toast("Cadastro atualizado!")
                st.rerun()
            else:
                st.info("Nenhuma alteração identificada.")
        except (ValueError, PermissionError) as erro:
            st.error(str(erro))

    st.divider()

    # Fotografia
    st.write("#### Fotografia")

    nova_foto = st.file_uploader(
        "Adicionar ou substituir fotografia",
        type=["jpg", "jpeg", "png", "webp"],
        key=f"foto_editar_voluntario_{voluntario_id}",
    )

    if st.button(
        "Salvar fotografia",
        disabled=nova_foto is None,
        key=f"salvar_foto_voluntario_{voluntario_id}",
    ):
        try:
            alterou = salvar_foto_voluntario(
                voluntario_id,
                nova_foto.getvalue(),
                ator_id=ator_id,
            )
            if alterou:
                st.toast("Fotografia atualizada!")
                st.rerun()
            else:
                st.info("A fotografia já está cadastrada.")
        except (ValueError, PermissionError) as erro:
            st.error(str(erro))

    if foto_atual and st.button(
        "Remover fotografia",
        key=f"remover_foto_voluntario_{voluntario_id}",
    ):
        try:
            remover_foto_voluntario(voluntario_id, ator_id=ator_id)
            st.toast("Fotografia removida!")
            st.rerun()
        except (ValueError, PermissionError) as erro:
            st.error(str(erro))

    st.divider()

    # Situação
    st.write("#### Situação do voluntário")

    if voluntario["ativo"]:
        texto_acao = "Desativar voluntário"
        nova_situacao = False
    else:
        texto_acao = "Reativar voluntário"
        nova_situacao = True

    if st.button(
        texto_acao,
        key=f"situacao_voluntario_{voluntario_id}",
    ):
        try:
            alterar_situacao_voluntario(
                voluntario_id,
                nova_situacao,
                ator_id=ator_id,
            )
            st.toast("Situação atualizada!")
            st.rerun()
        except (ValueError, PermissionError) as erro:
            st.error(str(erro))

    # Exclusão restrita
    if not tem_permissao(perfil, "excluir_voluntarios"):
        return

    st.divider()
    st.write("#### Exclusão definitiva")

    with conectar() as conexao:
        total_presencas = conexao.execute(
            """
            SELECT COUNT(*)
            FROM presencas_voluntarios
            WHERE voluntario_id = ?
            """,
            (voluntario_id,),
        ).fetchone()[0]

    if total_presencas:
        st.warning(
            f"Este voluntário possui {total_presencas} "
            "presença(s). Para preservar o histórico, "
            "desative o cadastro em vez de excluí-lo."
        )
        return

    confirmar = st.checkbox(
        "Confirmo a exclusão definitiva deste voluntário.",
        key=f"confirmar_exclusao_voluntario_{voluntario_id}",
    )

    if st.button(
        "Excluir voluntário",
        disabled=not confirmar,
        key=f"excluir_voluntario_{voluntario_id}",
    ):
        try:
            excluir_voluntario(voluntario_id, ator_id=ator_id)
            st.session_state.pop("cadastro_voluntario_selecionado", None)
            st.toast("Voluntário excluído!")
            st.rerun()

        except (ValueError, PermissionError) as erro:
            st.error(str(erro))
