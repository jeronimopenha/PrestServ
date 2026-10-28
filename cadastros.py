import streamlit as st

from database import (
    cadastrar_pessoa,
    atualizar_pessoa,
    alterar_status_pessoa,
    listar_pessoas_admin,
    buscar_pessoa,
    buscar_foto,
    salvar_foto,
    remover_foto,
)
from fotos import converter_para_jpeg


def campo_texto(valor):
    return valor or ""


def salvar_imagem(pessoa_id, arquivo):
    if arquivo is not None:
        foto_jpeg = converter_para_jpeg(arquivo)
        salvar_foto(pessoa_id, foto_jpeg)


def tela_cadastros():
    st.subheader("Cadastro de pessoas atendidas")

    aba_novo, aba_editar = st.tabs(["Novo cadastro", "Consultar / editar"])

    with aba_novo:
        novo_cadastro()

    with aba_editar:
        editar_cadastro()


def novo_cadastro():
    st.write("### Cadastrar pessoa")

    with st.form("form_nova_pessoa", clear_on_submit=True):
        nome = st.text_input("Nome completo *")
        documento = st.text_input("Documento")
        telefone = st.text_input("Telefone")
        contato_nome = st.text_input("Nome do contato")
        contato_telefone = st.text_input("Telefone do contato")

        foto = st.file_uploader(
            "Fotografia", type=["jpg", "jpeg", "png", "webp"], key="foto_nova"
        )

        enviar = st.form_submit_button(
            "Cadastrar pessoa", type="primary", use_container_width=True
        )

    if enviar:
        try:
            # Valida a imagem antes de criar o cadastro.
            foto_jpeg = converter_para_jpeg(foto) if foto is not None else None

            pessoa_id = cadastrar_pessoa(
                nome, documento, telefone, contato_nome, contato_telefone
            )

            if foto_jpeg is not None:
                salvar_foto(pessoa_id, foto_jpeg)

            st.success(f"Pessoa cadastrada com sucesso! ID: {pessoa_id}")

        except ValueError as erro:
            st.error(str(erro))


def editar_cadastro():
    pessoas = listar_pessoas_admin()

    if not pessoas:
        st.info("Nenhuma pessoa cadastrada.")
        return

    opcoes = {
        p["id"]: (
            f"{p['nome']} (ID {p['id']})" + (" [Inativo]" if not p["ativo"] else "")
        )
        for p in pessoas
    }

    pessoa_id = st.selectbox(
        "Selecione a pessoa",
        options=list(opcoes.keys()),
        format_func=lambda id: opcoes[id],
        index=None,
        placeholder="Digite ou selecione uma pessoa...",
        key="cadastro_pessoa_id",
    )

    if pessoa_id is None:
        return

    pessoa = buscar_pessoa(pessoa_id)

    if pessoa is None:
        st.error("Cadastro não encontrado.")
        return

    # Mostra a fotografia existente.
    foto_atual = buscar_foto(pessoa_id)

    if foto_atual:
        st.image(foto_atual, width=180)
    else:
        st.caption("Sem fotografia cadastrada.")

    st.caption(f"Identificador do cadastro: {pessoa_id}")

    # A chave do formulário muda quando a pessoa muda,
    # evitando reutilizar dados de outro cadastro.
    with st.form(f"editar_pessoa_{pessoa_id}"):
        nome = st.text_input("Nome completo *", value=campo_texto(pessoa["nome"]))
        documento = st.text_input("Documento", value=campo_texto(pessoa["documento"]))
        telefone = st.text_input("Telefone", value=campo_texto(pessoa["telefone"]))
        contato_nome = st.text_input(
            "Nome do contato", value=campo_texto(pessoa["contato_nome"])
        )
        contato_telefone = st.text_input(
            "Telefone do contato", value=campo_texto(pessoa["contato_telefone"])
        )

        nova_foto = st.file_uploader(
            "Substituir fotografia",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"foto_edicao_{pessoa_id}",
        )

        salvar = st.form_submit_button(
            "Salvar alterações", type="primary", use_container_width=True
        )

    if salvar:
        try:
            foto_jpeg = (
                converter_para_jpeg(nova_foto) if nova_foto is not None else None
            )

            atualizar_pessoa(
                pessoa_id, nome, documento, telefone, contato_nome, contato_telefone
            )

            if foto_jpeg is not None:
                salvar_foto(pessoa_id, foto_jpeg)

            st.toast("Cadastro atualizado com sucesso!")
            st.rerun()

        except ValueError as erro:
            st.error(str(erro))

    st.divider()

    st.write("### Situação do cadastro")

    if pessoa["ativo"]:
        st.success("Cadastro ativo")

        if st.button("Desativar pessoa", key=f"desativar_{pessoa_id}"):
            alterar_status_pessoa(pessoa_id, False)
            st.rerun()
    else:
        st.warning("Cadastro inativo")

        if st.button("Reativar pessoa", key=f"reativar_{pessoa_id}"):
            alterar_status_pessoa(pessoa_id, True)
            st.rerun()

    if foto_atual:
        with st.expander("Remover fotografia"):
            confirmar = st.checkbox(
                "Confirmo que desejo remover a fotografia.",
                key=f"confirmar_foto_{pessoa_id}",
            )

            if st.button(
                "Remover fotografia",
                disabled=not confirmar,
                key=f"remover_foto_{pessoa_id}",
            ):
                remover_foto(pessoa_id)
                st.toast("Fotografia removida.")
                st.rerun()
