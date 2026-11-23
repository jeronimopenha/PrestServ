from datetime import date, timedelta

import streamlit as st

from conn.database import (
    data_atual,
    listar_pessoas_admin,
    conectar,
    registrar_log,
)
from model.consultas_relatorios import (
    indicadores,
    presencas_detalhadas,
    servicos_por_tipo,
    frequencia_pessoas,
    evolucao_diaria,
    evolucao_mensal,
    pessoas_ausentes,
    qualidade_cadastros,
)
from services.pdf_relatorios import gerar_pdf
from security.permissoes import exigir_permissao_usuario

COLUNAS_RELATORIO = {
    "id": "ID",
    "pessoa_id": "ID da pessoa",
    "presenca_id": "ID da presença",
    "pessoa": "Pessoa",
    "nome": "Nome",
    "data": "Data",
    "servico": "Serviço",
    "servicos": "Serviços",
    "quantidade": "Quantidade",
    "quantidade_servicos": "Qtd. de serviços",
    "presencas": "Presenças",
    "pessoas_distintas": "Pessoas distintas",
    "primeira_no_periodo": "Primeira presença",
    "ultima_no_periodo": "Última presença",
    "registrado_em": "Registrado em",
    "ultima_presenca": "Última presença",
    "dias_sem_comparecer": "Dias sem comparecer",
    "mes": "Mês",
    "documento": "Documento",
    "telefone": "Telefone",
    "fotografia": "Fotografia",
    "unidades": "Unidades distribuídas",
    "unidades_servicos": "Unidades distribuídas",
}


def tabela_relatorio(df):
    exibicao = df.rename(columns=COLUNAS_RELATORIO)

    st.dataframe(
        exibicao,
        hide_index=True,
        width="stretch",
    )


def inicio_mes(d):
    return d.replace(day=1)


def inicio_semestre(d):
    mes = 1 if d.month <= 6 else 7
    return d.replace(month=mes, day=1)


def inicio_ano(d):
    return d.replace(month=1, day=1)


def registrar_download_csv_relatorio(ator_id, nome_arquivo, total_linhas):
    """Registra a solicitação de exportação CSV."""

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(
            conexao,
            ator_id,
            "exportar_relatorios",
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao="exportar_relatorio_csv",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="relatorios",
            detalhes={
                "arquivo": nome_arquivo,
                "total_linhas": total_linhas,
            },
        )


def botao_csv(titulo, df, nome, ator_id):
    """
    Disponibiliza a exportação CSV de um relatório.

    Somente superadmin e admin podem exportar.
    """

    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "exportar_relatorios",
        )

    # Somente gera o arquivo após verificar a permissão.
    dados_csv = df.to_csv(
        index=False,
        sep=";",
    ).encode("utf-8-sig")

    st.download_button(
        titulo,
        data=dados_csv,
        file_name=nome,
        mime="text/csv",
        width="stretch",
        on_click=registrar_download_csv_relatorio,
        args=(ator_id, nome, len(df)),
    )


def registrar_download_pdf_relatorio(ator_id, tipo, inicio, fim, pessoa_id):
    """Registra a solicitação de download de um relatório PDF."""

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(
            conexao,
            ator_id,
            "exportar_relatorios",
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao="exportar_relatorio_pdf",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="relatorios",
            detalhes={
                "tipo": tipo,
                "inicio": inicio,
                "fim": fim,
                "pessoa_id": pessoa_id,
            },
        )


def tela_relatorios():
    ator_id = st.session_state["usuario"]["id"]

    # Recupera o perfil diretamente do banco.
    with conectar() as conexao:
        perfil = exigir_permissao_usuario(
            conexao,
            ator_id,
            "relatorios_gerais",
        )

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

    # Visualização restrita aos indicadores gerais.
    if perfil == "consulta":
        inicio_sql = inicio.isoformat()
        fim_sql = fim.isoformat()

        resumo = indicadores(
            inicio_sql,
            fim_sql,
            ator_id=ator_id,
        )

        por_servico = servicos_por_tipo(
            inicio_sql,
            fim_sql,
            ator_id=ator_id,
        )

        diaria = evolucao_diaria(
            inicio_sql,
            fim_sql,
            ator_id=ator_id,
        )

        mensal = evolucao_mensal(
            inicio_sql,
            fim_sql,
            ator_id=ator_id,
        )

        st.divider()
        st.write("### Indicadores gerais")

        c1, c2, c3 = st.columns(3)

        c1.metric("Pessoas distintas", resumo["pessoas"])
        c2.metric("Presenças", resumo["presencas"])
        c3.metric("Serviços registrados", resumo["servicos"])

        c4, c5, c6 = st.columns(3)

        c4.metric("Unidades distribuídas", resumo["unidades"])
        c5.metric("Dias com registros", resumo["dias_registrados"])
        c6.metric(
            "Média de presenças/dia registrado",
            f"{resumo['media_por_dia']:.2f}",
        )

        st.divider()
        st.write("### Serviços prestados")

        if not por_servico.empty:
            grafico_servicos(por_servico)
            tabela_relatorio(por_servico)
        else:
            st.info("Sem serviços registrados no período.")

        st.write("### Evolução diária")

        if not diaria.empty:
            grafico = diaria.copy()
            grafico["data"] = grafico["data"].astype("datetime64[ns]")

            st.line_chart(grafico.set_index("data")["presencas"])

        st.write("### Evolução mensal")

        if not mensal.empty:
            tabela_relatorio(mensal)
        else:
            st.info("Sem atendimentos registrados no período.")

        # Impede o acesso ao restante da página.
        # Não carrega cadastros, relatórios pessoais
        # nem disponibiliza exportações.
        return

    pessoas = listar_pessoas_admin(ator_id=st.session_state["usuario"]["id"])
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

    resumo = indicadores(
        inicio_sql,
        fim_sql,
        pessoa_id,
        ator_id=st.session_state["usuario"]["id"],
    )
    detalhado = presencas_detalhadas(
        inicio_sql,
        fim_sql,
        pessoa_id,
        ator_id=st.session_state["usuario"]["id"],
    )
    por_servico = servicos_por_tipo(
        inicio_sql,
        fim_sql,
        pessoa_id,
        ator_id=st.session_state["usuario"]["id"],
    )
    frequencia = frequencia_pessoas(
        inicio_sql,
        fim_sql,
        pessoa_id,
        ator_id=st.session_state["usuario"]["id"],
    )
    diaria = evolucao_diaria(
        inicio_sql,
        fim_sql,
        pessoa_id,
        ator_id=st.session_state["usuario"]["id"],
    )
    mensal = evolucao_mensal(
        inicio_sql,
        fim_sql,
        pessoa_id,
        ator_id=st.session_state["usuario"]["id"],
    )

    st.divider()

    c1, c2, c3 = st.columns(3)

    c1.metric("Pessoas distintas", resumo["pessoas"])
    c2.metric("Presenças", resumo["presencas"])
    c3.metric("Serviços registrados", resumo["servicos"])

    c4, c5, c6 = st.columns(3)

    c4.metric("Unidades distribuídas", resumo["unidades"])
    c5.metric("Dias com registros", resumo["dias_registrados"])
    c6.metric(
        "Média de presenças/dia registrado",
        f"{resumo['media_por_dia']:.2f}",
    )

    st.divider()

    abas = st.tabs(["Visão geral", "Frequência", "Histórico", "Ausências", "Cadastros"])

    with abas[0]:
        st.write("### Serviços prestados")

        if not por_servico.empty:
            grafico_servicos(por_servico)
            tabela_relatorio(por_servico)

            botao_csv(
                "Exportar serviços (CSV)",
                por_servico,
                "prestserv_servicos.csv",
                ator_id=st.session_state["usuario"]["id"],
            )
        else:
            st.info("Sem serviços registrados no período.")

        st.write("### Evolução diária")

        if not diaria.empty:
            grafico = diaria.copy()
            grafico["data"] = grafico["data"].astype("datetime64[ns]")
            st.line_chart(grafico.set_index("data")["presencas"])

        st.write("### Evolução mensal")

        if not mensal.empty:
            tabela_relatorio(mensal)

    with abas[1]:
        st.write("### Frequência por pessoa")
        tabela_relatorio(frequencia)
        botao_csv(
            "Exportar frequência (CSV)",
            frequencia,
            "prestserv_frequencia.csv",
            ator_id=st.session_state["usuario"]["id"],
        )
    with abas[2]:
        st.write("### Histórico de atendimentos")
        tabela_relatorio(detalhado)
        botao_csv(
            "Exportar histórico (CSV)",
            detalhado,
            "prestserv_historico.csv",
            ator_id=st.session_state["usuario"]["id"],
        )

    with abas[3]:
        st.write("### Pessoas sem atendimento recente")
        st.caption(
            "Considera pessoas ativas e atendimentos " "até a data final selecionada."
        )

        dias = st.number_input(
            "Dias sem comparecimento", min_value=1, max_value=3650, value=30
        )

        ausentes = pessoas_ausentes(
            fim_sql,
            dias,
            ator_id=st.session_state["usuario"]["id"],
        )

        tabela_relatorio(ausentes)

        botao_csv(
            "Exportar ausências (CSV)",
            ausentes,
            "prestserv_ausencias.csv",
            ator_id=st.session_state["usuario"]["id"],
        )

    with abas[4]:
        st.write("### Qualidade dos cadastros")

        qualidade = qualidade_cadastros(ator_id=st.session_state["usuario"]["id"])

        tabela_relatorio(qualidade)

        botao_csv(
            "Exportar cadastros (CSV)",
            qualidade,
            "prestserv_cadastros.csv",
            ator_id=st.session_state["usuario"]["id"],
        )

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

    pdf = gerar_pdf(
        tipo_pdf,
        inicio,
        fim,
        resumo,
        tabelas_pdf[tipo_pdf],
        ator_id=st.session_state["usuario"]["id"],
    )

    st.download_button(
        "Baixar relatório em PDF",
        data=pdf,
        file_name=(f"prestserv_relatorio_{inicio_sql}_{fim_sql}.pdf"),
        mime="application/pdf",
        type="primary",
        width="stretch",
        on_click=registrar_download_pdf_relatorio,
        args=(
            ator_id,
            tipo_pdf,
            inicio_sql,
            fim_sql,
            pessoa_id,
        ),
    )


def grafico_servicos(df):
    """
    Exibe registros de serviços e unidades distribuídas.
    Utiliza somente dados agregados.
    """

    if df.empty:
        st.info("Sem serviços registrados no período.")
        return

    dados = df.set_index("servico")[["quantidade", "unidades"]].rename(
        columns={
            "quantidade": "Registros do serviço",
            "unidades": "Unidades distribuídas",
        }
    )

    st.bar_chart(dados)
