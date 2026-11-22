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
    listar_atendimentos_data,
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

    painel_atendimento = st.container()

    # Grade de atendimentos registrados na data.
    st.write("### Atendimentos do dia")

    atendimentos = listar_atendimentos_data(
        data,
        ator_id=st.session_state["usuario"]["id"],
    )

    if atendimentos:
        st.caption(
            "Clique em uma linha para consultar ou "
            "atualizar os serviços dessa pessoa."
        )

        dados_grade = [
            {
                "Pessoa": registro["pessoa"],
                "Serviços": registro["servicos"],
                "Unidades": registro["unidades"],
            }
            for registro in atendimentos
        ]

        # Exibe até 7 linhas antes de habilitar a rolagem.
        linhas_visiveis = min(len(atendimentos), 7)
        altura_grade = 40 + (linhas_visiveis * 35)

        evento = st.dataframe(
            dados_grade,
            hide_index=True,
            width="stretch",
            height=altura_grade,
            row_height=35,
            on_select="rerun",
            selection_mode="single-row",
            key=f"grade_atendimentos_{data}",
        )

        linhas = evento.selection.rows

        pessoa_grade_id = atendimentos[linhas[0]]["pessoa_id"] if linhas else None

        selecao = (data, pessoa_grade_id)

        # Só altera a pessoa quando a seleção da grade muda.
        # Isso evita sobrescrever a pesquisa manual.
        if st.session_state.get("ultima_selecao_grade") != selecao:
            st.session_state["ultima_selecao_grade"] = selecao

            if pessoa_grade_id is not None:
                ids_ativos = {p["id"] for p in pessoas}

                if pessoa_grade_id in ids_ativos:
                    st.session_state["pessoa_selecionada"] = pessoa_grade_id
                else:
                    st.warning(
                        "Esta pessoa está com cadastro inativo "
                        "e não pode receber novos atendimentos."
                    )

    else:
        st.info("Nenhum atendimento registrado nesta data.")
        st.session_state["ultima_selecao_grade"] = (data, None)

    st.divider()

    with painel_atendimento:
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
            servicos_marcados = {}

        servicos = listar_servicos(ator_id=st.session_state["usuario"]["id"])

        # Identifica a combinação pessoa + data.
        atendimento_atual = (pessoa_id, data)

        # Inicializa os campos ao trocar de pessoa ou data.
        if st.session_state.get("atendimento_atual") != atendimento_atual:
            for servico in servicos:
                servico_id = servico["id"]

                st.session_state[f"servico_{servico_id}"] = servico_id in servicos_marcados

                st.session_state[f"quantidade_{servico_id}"] = servicos_marcados.get(
                    servico_id, 1
                )

            st.session_state["atendimento_atual"] = atendimento_atual

        st.write("**Serviços utilizados:**")

        coluna_titulo, coluna_quantidade = st.columns(
            [2, 1],
            vertical_alignment="center",
        )

        with coluna_titulo:
            st.caption("Serviço")

        with coluna_quantidade:
            st.caption("Quantidade")

        selecionados = {}

        for servico in servicos:
            servico_id = servico["id"]

            col_servico, col_quantidade = st.columns(
                [2, 1],
                vertical_alignment="center",
                gap="small",
            )

            with col_servico:
                marcado = st.checkbox(
                    servico["nome"],
                    key=f"servico_{servico_id}",
                )

            with col_quantidade:
                quantidade = st.number_input(
                    f"Quantidade de {servico['nome']}",
                    min_value=1,
                    step=1,
                    key=f"quantidade_{servico_id}",
                    disabled=not marcado,
                    label_visibility="collapsed",
                )

            if marcado:
                selecionados[servico_id] = int(quantidade)

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
