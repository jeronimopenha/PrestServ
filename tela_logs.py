import json
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from database import listar_logs, listar_acoes_logs, excluir_logs

FUSO = ZoneInfo("America/Sao_Paulo")


def converter_data_utc(data):
    """Converte uma data local para o formato UTC do SQLite."""
    instante = datetime.combine(data, time.min, tzinfo=FUSO)
    instante = instante.astimezone(timezone.utc)

    return instante.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def formatar_data(valor):
    """Converte a data UTC do log para horário de Brasília."""
    if not valor:
        return ""

    data = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    return data.astimezone(FUSO).strftime("%d/%m/%Y %H:%M:%S")


def tela_logs():
    st.subheader("Logs do sistema")
    st.caption("Histórico das operações realizadas no PrestServ.")

    ator = st.session_state["usuario"]

    st.write("### Filtros")

    col1, col2 = st.columns(2)

    with col1:
        operador = st.text_input("Operador", placeholder="Login do usuário")

    with col2:
        acoes = listar_acoes_logs(ator["id"])

        acao = st.selectbox(
            "Ação",
            options=[None] + acoes,
            format_func=lambda x: (
                "Todas as ações" if x is None else x.replace("_", " ").capitalize()
            ),
        )

    col3, col4 = st.columns(2)

    with col3:
        resultado = st.selectbox(
            "Resultado",
            ["Todos", "sucesso", "falha"],
        )

    with col4:
        limite = st.selectbox(
            "Máximo de registros",
            [50, 100, 200, 500, 1000],
            index=2,
        )

    filtrar_periodo = st.checkbox("Filtrar por período")

    inicio = None
    fim = None

    if filtrar_periodo:
        hoje = datetime.now(FUSO).date()

        c1, c2 = st.columns(2)

        with c1:
            data_inicial = st.date_input(
                "Data inicial",
                value=hoje - timedelta(days=30),
                format="DD/MM/YYYY",
            )

        with c2:
            data_final = st.date_input(
                "Data final",
                value=hoje,
                format="DD/MM/YYYY",
            )

        if data_inicial > data_final:
            st.error("A data inicial não pode superar a final.")
            return

        inicio = converter_data_utc(data_inicial)

        # O limite superior é exclusivo.
        fim = converter_data_utc(data_final + timedelta(days=1))

    registros = listar_logs(
        ator_id=ator["id"],
        limite=limite,
        inicio=inicio,
        fim=fim,
        operador=operador or None,
        acao=acao or None,
        resultado=None if resultado == "Todos" else resultado,
    )

    st.divider()

    st.write("### Registros encontrados")
    st.metric("Logs exibidos", len(registros))

    if not registros:
        st.info("Nenhum registro encontrado com os filtros informados.")
        return

    dados = []

    for registro in registros:
        dados.append(
            {
                "ID": registro["id"],
                "Data e hora": formatar_data(registro["criado_em"]),
                "Operador": registro["usuario_login"] or "Sistema",
                "Ação": registro["acao"],
                "Entidade": registro["entidade"] or "",
                "ID afetado": registro["entidade_id"],
                "Resultado": registro["resultado"],
            }
        )

    df = pd.DataFrame(dados)

    # Reinicia a seleção quando os registros exibidos mudam.
    assinatura = tuple(df["ID"].tolist())

    if st.session_state.get("logs_assinatura") != assinatura:
        st.session_state["logs_assinatura"] = assinatura
        st.session_state["logs_editor_versao"] = (
            st.session_state.get("logs_editor_versao", 0) + 1
        )
        st.session_state["logs_selecionar_todos"] = False

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Selecionar todos", use_container_width=True):
            st.session_state["logs_selecionar_todos"] = True
            st.session_state["logs_editor_versao"] += 1

    with c2:
        if st.button("Limpar seleção", use_container_width=True):
            st.session_state["logs_selecionar_todos"] = False
            st.session_state["logs_editor_versao"] += 1

    df.insert(
        0,
        "Selecionar",
        st.session_state["logs_selecionar_todos"],
    )

    versao_editor = st.session_state["logs_editor_versao"]

    tabela_editada = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        disabled=[coluna for coluna in df.columns if coluna != "Selecionar"],
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(
                "Selecionar",
                help="Marque os registros que deseja excluir.",
                default=False,
                required=True,
            ),
        },
        key=f"editor_logs_{versao_editor}",
    )

    ids_selecionados = [
        int(id)
        for id in tabela_editada.loc[tabela_editada["Selecionar"], "ID"].tolist()
    ]

    st.caption(
        f"{len(ids_selecionados)} registro(s) selecionado(s). "
        "Limite de 500 exclusões por operação."
    )

    st.write("### Excluir logs selecionados")

    quantidade = len(ids_selecionados)
    selecao_valida = 0 < quantidade <= 500

    if quantidade > 500:
        st.warning(
            "É permitido excluir no máximo 500 registros "
            "por operação. Reduza a seleção."
        )

    confirmar = st.checkbox(
        "Confirmo que desejo excluir definitivamente " "os registros selecionados.",
        disabled=not selecao_valida,
        key=f"confirmar_exclusao_logs_{versao_editor}",
    )

    if st.button(
        "Excluir selecionados",
        disabled=not selecao_valida or not confirmar,
        type="secondary",
        use_container_width=True,
    ):
        try:
            total = excluir_logs(
                ids_selecionados,
                ator_id=ator["id"],
            )

            st.session_state["logs_editor_versao"] += 1
            st.session_state["logs_selecionar_todos"] = False
            st.session_state.pop("logs_assinatura", None)

            st.toast(f"{total} registro(s) excluído(s) com sucesso!")
            st.rerun()

        except (ValueError, PermissionError) as erro:
            st.error(str(erro))

    st.caption("Datas e horários apresentados no fuso de Brasília.")

    st.divider()
    st.write("### Detalhes da operação")

    opcoes = {r["id"]: r for r in registros}

    log_id = st.selectbox(
        "Selecione um registro",
        options=list(opcoes),
        index=None,
        placeholder="Selecione o ID do log...",
        format_func=lambda id: (
            f"#{id} — {opcoes[id]['acao']} "
            f"({formatar_data(opcoes[id]['criado_em'])})"
        ),
    )

    if log_id is not None:
        registro = opcoes[log_id]

        st.write(f"**Operador:** {registro['usuario_login'] or 'Sistema'}")
        st.write(f"**Ação:** {registro['acao']}")
        st.write(f"**Resultado:** {registro['resultado']}")
        st.write(f"**Entidade:** {registro['entidade'] or '-'}")
        st.write(f"**ID afetado:** {registro['entidade_id']}")

        if registro["detalhes_json"]:
            try:
                st.json(json.loads(registro["detalhes_json"]))
            except json.JSONDecodeError:
                st.code(registro["detalhes_json"])
        else:
            st.info("Esta operação não possui detalhes adicionais.")
