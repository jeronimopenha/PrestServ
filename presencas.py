from datetime import date, datetime

import streamlit as st

from database import (
    data_atual,
    listar_pessoas,
    buscar_pessoa,
    listar_servicos,
    buscar_presenca,
    buscar_servicos_presenca,
    salvar_atendimento,
    total_presencas,
    buscar_foto,
)


def tela_presencas():
    st.subheader("Registro de presenças")

    hoje = date.fromisoformat(data_atual())
    perfil = st.session_state["usuario"]["perfil"]

    # O porteiro trabalha exclusivamente na data atual.
    if perfil == "porteiro":
        st.session_state["data_atendimento"] = hoje

    elif "data_atendimento" not in st.session_state:
        st.session_state["data_atendimento"] = hoje

    data_selecionada = st.date_input(
        "Data do atendimento",
        key="data_atendimento",
        max_value=hoje,
        disabled=(perfil == "porteiro"),
        format="DD/MM/YYYY",
    )

    data = data_selecionada.isoformat()

    st.metric(
        "Presenças na data",
        total_presencas(
            data,
            ator_id=st.session_state["usuario"]["id"],
        ),
    )

    st.divider()

    # Seleção da pessoa
    pessoas = listar_pessoas(ator_id=st.session_state["usuario"]["id"])

    if not pessoas:
        st.warning("Nenhuma pessoa cadastrada.")
        return

    opcoes = {pessoa["id"]: pessoa["nome"] for pessoa in pessoas}

    pessoa_id = st.selectbox(
        "Selecione a pessoa",
        options=list(opcoes.keys()),
        format_func=lambda id: opcoes[id],
        index=None,
        placeholder="Digite ou selecione uma pessoa...",
        key="pessoa_selecionada",
    )

    if pessoa_id is None:
        st.info("Selecione uma pessoa para registrar o atendimento.")
        return

    pessoa = buscar_pessoa(
        pessoa_id,
        ator_id=st.session_state["usuario"]["id"],
    )

    if pessoa is None:
        st.error("Pessoa não encontrada.")
        return

    col_foto, col_dados = st.columns([1, 2])

    with col_foto:
        foto = buscar_foto(
            pessoa_id,
            ator_id=st.session_state["usuario"]["id"],
        )

        if foto:
            st.image(foto, width=150)
        else:
            st.caption("Sem fotografia")

    with col_dados:
        st.write(f"### {pessoa['nome']}")

        if pessoa["documento"]:
            st.caption(f"Documento: {pessoa['documento']}")

        if pessoa["telefone"]:
            st.caption(f"Telefone: {pessoa['telefone']}")

    # Consulta o atendimento na data selecionada.
    presenca = buscar_presenca(
        pessoa_id,
        data,
        ator_id=st.session_state["usuario"]["id"],
    )

    if presenca:
        st.success("Atendimento já registrado nesta data.")
        servicos_marcados = buscar_servicos_presenca(
            presenca["id"],
            ator_id=st.session_state["usuario"]["id"],
        )
    else:
        st.info("Nenhum atendimento registrado nesta data.")
        servicos_marcados = []

    servicos = listar_servicos(ator_id=st.session_state["usuario"]["id"])

    # Identifica a combinação pessoa + data.
    atendimento_atual = (pessoa_id, data)

    # Inicializa os checkboxes ao trocar de pessoa ou data.
    if st.session_state.get("atendimento_atual") != atendimento_atual:
        for servico in servicos:
            chave = f"servico_{servico['id']}"
            st.session_state[chave] = servico["id"] in servicos_marcados

        st.session_state["atendimento_atual"] = atendimento_atual

    st.write("**Serviços utilizados:**")

    selecionados = []

    for servico in servicos:
        marcado = st.checkbox(servico["nome"], key=f"servico_{servico['id']}")

        if marcado:
            selecionados.append(servico["id"])

    st.divider()

    if presenca:
        texto_botao = "Atualizar atendimento" if selecionados else "Remover atendimento"
    else:
        texto_botao = "Registrar atendimento"

    if st.button(
        texto_botao,
        type="primary",
        width="stretch",
        disabled=not presenca and not selecionados,
    ):
        try:
            ator = st.session_state["usuario"]

            salvar_atendimento(
                pessoa_id,
                selecionados,
                data,
                ator_id=ator["id"],
                ator_login=ator["login"],
            )

            # Recarrega os valores a partir do banco.
            st.session_state.pop("atendimento_atual", None)

            if selecionados:
                st.toast("Atendimento salvo com sucesso!")
            else:
                st.toast("Atendimento removido com sucesso!")

            # Não altera a data selecionada.
            st.rerun()

        except ValueError as erro:
            st.error(str(erro))
