"""Tela de registro de presenças dos voluntários."""

from datetime import date

import streamlit as st

from conn.database import conectar, data_atual
from security.permissoes import exigir_permissao_usuario, tem_permissao
from model.voluntarios import (
    listar_voluntarios,
    buscar_foto_voluntario,
    listar_presencas_voluntarios,
    registrar_presenca_voluntario,
    remover_presenca_voluntario,
)


def tela_presencas_voluntarios():
    usuario = st.session_state.get("usuario")

    if not usuario:
        st.error("Sessão não encontrada.")
        return

    ator_id = usuario["id"]

    try:
        with conectar() as conexao:
            perfil = exigir_permissao_usuario(
                conexao,
                ator_id,
                "registrar_presenca_voluntarios",
            )
    except PermissionError as erro:
        st.error(str(erro))
        return

    st.subheader("Presenças dos voluntários")

    hoje = date.fromisoformat(data_atual())

    pode_alterar_data = tem_permissao(
        perfil,
        "alterar_data_presenca_voluntarios",
    )

    if pode_alterar_data:
        data = st.date_input(
            "Data da presença",
            value=hoje,
            max_value=hoje,
            format="DD/MM/YYYY",
            key="data_presencas_voluntarios",
        )
    else:
        data = hoje
        st.caption(f"Data: {hoje:%d/%m/%Y}")

    data_iso = data.isoformat()

    try:
        voluntarios = listar_voluntarios(
            ator_id=ator_id,
            somente_ativos=True,
        )

        presentes = listar_presencas_voluntarios(
            data_iso,
            ator_id=ator_id,
        )

    except (ValueError, PermissionError) as erro:
        st.error(str(erro))
        return

    presentes_ids = {registro["voluntario_id"] for registro in presentes}

    disponiveis = [
        voluntario
        for voluntario in voluntarios
        if voluntario["id"] not in presentes_ids
    ]

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        st.metric("Presentes na data", len(presentes))

    with coluna2:
        st.metric("Voluntários ativos", len(voluntarios))

    st.divider()

    # Registro de presença.
    st.write("#### Registrar presença")

    if not disponiveis:
        st.info("Não há voluntários disponíveis para " "registrar nesta data.")
    else:
        opcoes = {voluntario["id"]: voluntario["nome"] for voluntario in disponiveis}

        voluntario_id = st.selectbox(
            "Selecione o voluntário",
            options=list(opcoes),
            format_func=lambda vid: opcoes[vid],
            index=None,
            placeholder="Digite ou selecione um nome...",
            key=f"selecionar_voluntario_presenca_{data_iso}",
        )

        if voluntario_id is not None:
            try:
                foto = buscar_foto_voluntario(
                    voluntario_id,
                    ator_id=ator_id,
                )
            except PermissionError as erro:
                st.error(str(erro))
                return

            if foto:
                st.image(foto, width=180)
            else:
                st.caption("Voluntário sem fotografia.")

            if st.button(
                "Registrar presença",
                type="primary",
                width="stretch",
                key=f"registrar_voluntario_{data_iso}",
            ):
                try:
                    registrou = registrar_presenca_voluntario(
                        voluntario_id,
                        data_iso,
                        ator_id=ator_id,
                    )

                    if registrou:
                        st.toast("Presença registrada!")
                    else:
                        st.toast("Presença já registrada.")

                    st.rerun()

                except (ValueError, PermissionError) as erro:
                    st.error(str(erro))

    st.divider()

    # Relação de presenças.
    st.write("#### Voluntários presentes")

    if not presentes:
        st.info("Nenhuma presença registrada nesta data.")
        return

    tabela = [
        {
            "ID": registro["voluntario_id"],
            "Voluntário": registro["nome"],
            "Situação": ("Ativo" if registro["ativo"] else "Inativo"),
        }
        for registro in presentes
    ]

    # A chave muda quando muda a composição das presenças,
    # evitando manter uma seleção de linhas desatualizada.
    assinatura = "_".join(str(registro["id"]) for registro in presentes)

    evento = st.dataframe(
        tabela,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        key=f"grade_voluntarios_{data_iso}_{assinatura}",
    )

    selecionadas = evento.selection.rows

    if not selecionadas:
        st.caption(
            "Selecione uma linha da tabela para " "consultar ou remover a presença."
        )
        return

    indice = selecionadas[0]

    if indice >= len(presentes):
        return

    selecionado = presentes[indice]

    st.write(f"**Selecionado:** {selecionado['nome']}")

    # O porteiro não pode alterar voluntários inativos.
    if perfil == "porteiro" and not selecionado["ativo"]:
        st.warning("Não é permitido alterar a presença " "de um voluntário inativo.")
        return

    if st.button(
        "Remover presença selecionada",
        width="stretch",
        key=(f"remover_presenca_voluntario_" f"{data_iso}_{selecionado['id']}"),
    ):
        try:
            removeu = remover_presenca_voluntario(
                selecionado["voluntario_id"],
                data_iso,
                ator_id=ator_id,
            )

            if removeu:
                st.toast("Presença removida!")
            else:
                st.toast("Presença não encontrada.")

            st.rerun()

        except (ValueError, PermissionError) as erro:
            st.error(str(erro))
