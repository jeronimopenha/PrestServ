from datetime import date, timedelta

import streamlit as st

from database import data_atual, listar_pessoas_admin
from consultas_relatorios import (
    indicadores,
    presencas_detalhadas,
    servicos_por_tipo,
    frequencia_pessoas,
    evolucao_diaria,
    evolucao_mensal,
    pessoas_ausentes,
    qualidade_cadastros,
)
from pdf_relatorios import gerar_pdf


def inicio_mes(d):
    return d.replace(day=1)


def inicio_semestre(d):
    mes = 1 if d.month <= 6 else 7
    return d.replace(month=mes, day=1)


def inicio_ano(d):
    return d.replace(month=1, day=1)


def botao_csv(titulo, df, nome):
    st.download_button(
        titulo,
        data=df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig"),
        file_name=nome,
        mime="text/csv",
        use_container_width=True,
    )


def tela_relatorios():
    st.subheader("Relatórios")

    hoje = date.fromisoformat(data_atual())

    periodo = st.selectbox(
        "Período", ["Mês atual", "Semestre atual", "Ano atual", "Personalizado"]
    )

    if periodo == "Mês atual":
        inicio, fim = inicio_mes(hoje), hoje
    elif periodo == "Semestre atual":
        inicio, fim = inicio_semestre(hoje), hoje
    elif periodo == "Ano atual":
        inicio, fim = inicio_ano(hoje), hoje
    else:
        col1, col2 = st.columns(2)
        with col1:
            inicio = st.date_input(
                "Data inicial", value=inicio_mes(hoje), format="DD/MM/YYYY"
            )
        with col2:
            fim = st.date_input("Data final", value=hoje, format="DD/MM/YYYY")

    if inicio > fim:
        st.error("A data inicial não pode superar a final.")
        return

    pessoas = listar_pessoas_admin()
    opcoes = {p["id"]: p["nome"] for p in pessoas}

    pessoa_id = st.selectbox(
        "Filtrar por pessoa",
        options=[None] + list(opcoes.keys()),
        format_func=lambda id: (
            "Todas as pessoas" if id is None else f"{opcoes[id]} (ID {id})"
        ),
    )

    inicio_sql = inicio.isoformat()
    fim_sql = fim.isoformat()

    resumo = indicadores(inicio_sql, fim_sql, pessoa_id)
    detalhado = presencas_detalhadas(inicio_sql, fim_sql, pessoa_id)
    por_servico = servicos_por_tipo(inicio_sql, fim_sql, pessoa_id)
    frequencia = frequencia_pessoas(inicio_sql, fim_sql, pessoa_id)
    diaria = evolucao_diaria(inicio_sql, fim_sql, pessoa_id)
    mensal = evolucao_mensal(inicio_sql, fim_sql, pessoa_id)

    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("Pessoas distintas", resumo["pessoas"])
    c2.metric("Presenças", resumo["presencas"])
    c3.metric("Serviços prestados", resumo["servicos"])

    c4, c5 = st.columns(2)
    c4.metric("Dias com registros", resumo["dias_registrados"])
    c5.metric("Média de presenças/dia registrado", f"{resumo['media_por_dia']:.2f}")

    st.divider()

    abas = st.tabs(["Visão geral", "Frequência", "Histórico", "Ausências", "Cadastros"])

    with abas[0]:
        st.write("### Serviços prestados")

        if not por_servico.empty:
            st.bar_chart(por_servico.set_index("servico")["quantidade"])
            st.dataframe(por_servico, hide_index=True, use_container_width=True)
        else:
            st.info("Sem serviços registrados no período.")

        st.write("### Evolução diária")

        if not diaria.empty:
            grafico = diaria.copy()
            grafico["data"] = grafico["data"].astype("datetime64[ns]")
            st.line_chart(grafico.set_index("data")["presencas"])

        st.write("### Evolução mensal")

        if not mensal.empty:
            st.dataframe(mensal, hide_index=True, use_container_width=True)

    with abas[1]:
        st.write("### Frequência por pessoa")
        st.dataframe(frequencia, hide_index=True, use_container_width=True)
        botao_csv("Exportar frequência (CSV)", frequencia, "prestserv_frequencia.csv")

    with abas[2]:
        st.write("### Histórico de atendimentos")
        st.dataframe(detalhado, hide_index=True, use_container_width=True)
        botao_csv("Exportar histórico (CSV)", detalhado, "prestserv_historico.csv")

    with abas[3]:
        st.write("### Pessoas sem atendimento recente")
        st.caption(
            "Considera pessoas ativas e atendimentos " "até a data final selecionada."
        )

        dias = st.number_input(
            "Dias sem comparecimento", min_value=1, max_value=3650, value=30
        )

        ausentes = pessoas_ausentes(fim_sql, dias)

        st.dataframe(ausentes, hide_index=True, use_container_width=True)

        botao_csv("Exportar ausências (CSV)", ausentes, "prestserv_ausencias.csv")

    with abas[4]:
        st.write("### Qualidade dos cadastros")

        qualidade = qualidade_cadastros()

        st.dataframe(qualidade, hide_index=True, use_container_width=True)

        botao_csv("Exportar cadastros (CSV)", qualidade, "prestserv_cadastros.csv")

    st.divider()
    st.write("### Exportar relatório em PDF")

    tipo_pdf = st.selectbox(
        "Conteúdo do PDF",
        [
            "Relatório geral",
            "Frequência por pessoa",
            "Histórico detalhado",
            "Serviços prestados",
        ],
    )

    tabelas_pdf = {
        "Relatório geral": [
            ("Serviços prestados", por_servico),
            ("Evolução mensal", mensal),
            ("Frequência por pessoa", frequencia),
        ],
        "Frequência por pessoa": [("Frequência por pessoa", frequencia)],
        "Histórico detalhado": [("Histórico de atendimentos", detalhado)],
        "Serviços prestados": [("Serviços prestados", por_servico)],
    }

    pdf = gerar_pdf(tipo_pdf, inicio, fim, resumo, tabelas_pdf[tipo_pdf])

    st.download_button(
        "Baixar relatório em PDF",
        data=pdf,
        file_name=(f"prestserv_relatorio_{inicio_sql}_{fim_sql}.pdf"),
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
