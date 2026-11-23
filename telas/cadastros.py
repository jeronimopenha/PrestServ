import streamlit as st

from conn.database import (
    conectar,
    cadastrar_pessoa,
    atualizar_pessoa,
    alterar_status_pessoa,
    listar_pessoas_admin,
    buscar_pessoa,
    buscar_foto,
    salvar_foto,
    remover_foto,
    excluir_pessoa,
)

from bd_schemes.estrutura_v110 import consultar_vinculos
from model.fotos import converter_para_jpeg
from security.permissoes import exigir_permissao_usuario, tem_permissao


def campo_texto(valor):
    return valor or ""


def salvar_imagem(pessoa_id, arquivo):
    if arquivo is not None:
        foto_jpeg = converter_para_jpeg(arquivo)
        salvar_foto(
            pessoa_id,
            foto_jpeg,
            ator_id=st.session_state["usuario"]["id"],
            ator_login=st.session_state["usuario"]["login"],
        )


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

        endereco = st.text_input("Endereço")

        observacoes = st.text_area(
            "Observações",
            placeholder="Informações adicionais sobre a pessoa atendida",
        )

        autorizado_refeicao_local = st.selectbox(
            "Autorização para realizar refeições no recinto",
            options=[None, 1, 0],
            format_func=lambda valor: {
                None: "Não informado",
                1: "Autorizado",
                0: "Não autorizado",
            }[valor],
            help=(
                "Essa informação não impede a prestação "
                "de serviços. Apenas identifica se a pessoa "
                "pode realizar refeições dentro do recinto."
            ),
        )

        foto = st.file_uploader(
            "Fotografia", type=["jpg", "jpeg", "png", "webp"], key="foto_nova"
        )

        enviar = st.form_submit_button(
            "Cadastrar pessoa",
            type="primary",
            width="stretch",
        )

    if enviar:
        try:
            # Valida a imagem antes de criar o cadastro.
            foto_jpeg = converter_para_jpeg(foto) if foto is not None else None

            ator = st.session_state["usuario"]

            pessoa_id = cadastrar_pessoa(
                nome,
                documento,
                telefone,
                contato_nome,
                contato_telefone,
                ator_id=ator["id"],
                ator_login=ator["login"],
                endereco=endereco,
                observacoes=observacoes,
                autorizado_refeicao_local=autorizado_refeicao_local,
            )

            if foto_jpeg is not None:
                salvar_foto(
                    pessoa_id,
                    foto_jpeg,
                    ator_id=st.session_state["usuario"]["id"],
                    ator_login=st.session_state["usuario"]["login"],
                )

            st.success(f"Pessoa cadastrada com sucesso! ID: {pessoa_id}")

        except ValueError as erro:
            st.error(str(erro))


def editar_cadastro():
    ator_id = st.session_state["usuario"]["id"]

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(
            conexao,
            ator_id,
            "consultar_dados_sensiveis",
        )

    pessoas = listar_pessoas_admin(ator_id=ator_id)

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

    pessoa = buscar_pessoa(
        pessoa_id,
        ator_id=st.session_state["usuario"]["id"],
    )

    if pessoa is None:
        st.error("Cadastro não encontrado.")
        return

    # Mostra a fotografia existente.
    foto_atual = buscar_foto(
        pessoa_id,
        ator_id=st.session_state["usuario"]["id"],
    )

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

        endereco = st.text_input(
            "Endereço",
            value=campo_texto(pessoa["endereco"]),
        )

        observacoes = st.text_area(
            "Observações",
            value=campo_texto(pessoa["observacoes"]),
        )

        opcoes_autorizacao = [None, 1, 0]

        autorizado_refeicao_local = st.selectbox(
            "Autorização para realizar refeições no recinto",
            options=opcoes_autorizacao,
            index=opcoes_autorizacao.index(pessoa["autorizado_refeicao_local"]),
            format_func=lambda valor: {
                None: "Não informado",
                1: "Autorizado",
                0: "Não autorizado",
            }[valor],
            help=(
                "Pessoas não autorizadas podem receber "
                "serviços externos normalmente."
            ),
        )

        nova_foto = st.file_uploader(
            "Substituir fotografia",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"foto_edicao_{pessoa_id}",
        )

        salvar = st.form_submit_button(
            "Salvar alterações",
            type="primary",
            width="stretch",
        )

    if salvar:
        try:
            foto_jpeg = (
                converter_para_jpeg(nova_foto) if nova_foto is not None else None
            )

            ator = st.session_state["usuario"]

            atualizar_pessoa(
                pessoa_id,
                nome,
                documento,
                telefone,
                contato_nome,
                contato_telefone,
                ator_id=ator["id"],
                ator_login=ator["login"],
                endereco=endereco,
                observacoes=observacoes,
                autorizado_refeicao_local=autorizado_refeicao_local,
            )

            if foto_jpeg is not None:
                salvar_foto(
                    pessoa_id,
                    foto_jpeg,
                    ator_id=st.session_state["usuario"]["id"],
                    ator_login=st.session_state["usuario"]["login"],
                )

            st.toast("Cadastro atualizado com sucesso!")
            st.rerun()

        except ValueError as erro:
            st.error(str(erro))

    st.divider()

    st.write("### Situação do cadastro")
    ator = st.session_state["usuario"]

    if pessoa["ativo"]:
        st.success("Cadastro ativo")

        if st.button("Desativar pessoa", key=f"desativar_{pessoa_id}"):
            alterar_status_pessoa(
                pessoa_id,
                False,
                ator["id"],
                ator["login"],
            )
            st.rerun()
    else:
        st.warning("Cadastro inativo")

        if st.button("Reativar pessoa", key=f"reativar_{pessoa_id}"):
            alterar_status_pessoa(
                pessoa_id,
                True,
                ator["id"],
                ator["login"],
            )
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
                remover_foto(
                    pessoa_id,
                    ator_id=st.session_state["usuario"]["id"],
                    ator_login=st.session_state["usuario"]["login"],
                )
                st.toast("Fotografia removida.")
                st.rerun()

    # Apenas superadmin e admin podem visualizar
    # as opções de exclusão definitiva.
    if not tem_permissao(perfil, "excluir_pessoas"):
        return

    st.divider()
    st.write("### Excluir cadastro")

    # Consulta os relacionamentos existentes.
    with conectar() as conexao:
        vinculos = consultar_vinculos(conexao, "pessoas", pessoa_id)

    pode_excluir = len(vinculos) == 0

    if not pode_excluir:
        st.warning(
            "Este cadastro possui relacionamentos e não "
            "pode ser excluído. Utilize a desativação."
        )

        for vinculo in vinculos:
            st.caption(f"{vinculo['tabela']}: " f"{vinculo['quantidade']} registro(s)")
    else:
        st.success("Este cadastro não possui relacionamentos " "e pode ser excluído.")

    confirmar_exclusao = st.checkbox(
        "Confirmo que desejo excluir definitivamente " "este cadastro.",
        disabled=not pode_excluir,
        key=f"confirmar_exclusao_{pessoa_id}",
    )

    if st.button(
        "Excluir pessoa",
        disabled=not pode_excluir or not confirmar_exclusao,
        key=f"excluir_pessoa_{pessoa_id}",
        type="secondary",
    ):
        try:
            ator = st.session_state["usuario"]

            excluir_pessoa(
                pessoa_id,
                ator_id=ator["id"],
            )

            st.session_state.pop("cadastro_pessoa_id", None)

            st.toast("Cadastro excluído com sucesso!")
            st.rerun()

        except ValueError as erro:
            st.error(str(erro))
