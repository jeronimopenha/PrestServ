"""Interface de relatórios dos voluntários."""

import csv
from io import StringIO
from datetime import date

import streamlit as st

from database import conectar, data_atual, registrar_log
from permissoes import exigir_permissao_usuario, tem_permissao
from consultas_voluntarios import (
    ranking_voluntarios,
    estatisticas_voluntarios,
    relatorio_cadastros_voluntarios,
    historico_presencas_voluntario,
    destaques_voluntarios,
)
from pdf_voluntarios import (
    gerar_pdf_ranking_voluntarios,
    gerar_pdf_cadastros_voluntarios,
    gerar_pdf_historico_voluntario,
)
from certificados_voluntarios import gerar_certificados_voluntarios


def _selecionar_periodo():
    """Retorna as datas inicial e final em formato ISO."""

    hoje = date.fromisoformat(data_atual())

    opcao = st.selectbox(
        "Período",
        [
            "Mês atual",
            "Semestre atual",
            "Ano atual",
            "Personalizado",
        ],
        key="periodo_relatorios_voluntarios",
    )

    if opcao == "Mês atual":
        inicio = date(hoje.year, hoje.month, 1)
        fim = hoje

    elif opcao == "Semestre atual":
        mes_inicial = 1 if hoje.month <= 6 else 7
        inicio = date(hoje.year, mes_inicial, 1)
        fim = hoje

    elif opcao == "Ano atual":
        inicio = date(hoje.year, 1, 1)
        fim = hoje

    else:
        col1, col2 = st.columns(2)

        with col1:
            inicio = st.date_input(
                "Data inicial",
                value=date(hoje.year, hoje.month, 1),
                max_value=hoje,
                format="DD/MM/YYYY",
                key="inicio_relatorios_voluntarios",
            )

        with col2:
            fim = st.date_input(
                "Data final",
                value=hoje,
                max_value=hoje,
                format="DD/MM/YYYY",
                key="fim_relatorios_voluntarios",
            )

    if inicio > fim:
        st.error("A data inicial não pode ser posterior à final.")
        return None

    st.caption(f"Período selecionado: " f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}")

    return inicio.isoformat(), fim.isoformat()


def _texto_csv_seguro(valor):
    """Evita a interpretação de nomes como fórmulas em planilhas."""

    texto = "" if valor is None else str(valor)

    if texto.lstrip().startswith(("=", "+", "-", "@")) or texto.startswith(
        ("\t", "\r", "\n")
    ):
        return "'" + texto

    return texto


def gerar_csv_ranking_voluntarios(ranking):
    """Gera o CSV do ranking, compatível com LibreOffice Calc."""

    saida = StringIO(newline="")

    escritor = csv.writer(
        saida,
        delimiter=";",
        lineterminator="\r\n",
    )

    escritor.writerow(
        [
            "Colocação",
            "Voluntário",
            "Presenças",
            "Situação",
        ]
    )

    for registro in ranking:
        escritor.writerow(
            [
                f"{registro['posicao']}º",
                _texto_csv_seguro(registro["nome"]),
                registro["presencas"],
                "Ativo" if registro["ativo"] else "Inativo",
            ]
        )

    return saida.getvalue().encode("utf-8-sig")


def registrar_download_csv_voluntarios(
    ator_id, tipo, inicio, fim, total_linhas, voluntario_id=None
):
    """Audita a solicitação de exportação CSV."""

    if tipo not in {"ranking", "cadastros", "historico"}:
        raise ValueError("Tipo de relatório inválido.")

    if tipo == "historico":
        if type(voluntario_id) is not int or voluntario_id <= 0:
            raise ValueError("Identificador de voluntário inválido.")
    elif voluntario_id is not None:
        raise ValueError("Identificador não permitido neste relatório.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(
            conexao,
            ator_id,
            "exportar_relatorios_voluntarios",
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao="exportar_relatorio_voluntarios_csv",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="voluntarios",
            detalhes={
                "tipo": tipo,
                "inicio": inicio,
                "fim": fim,
                "total_linhas": total_linhas,
                **({"voluntario_id": voluntario_id} if tipo == "historico" else {}),
            },
        )


def tela_relatorios_voluntarios():
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
                "estatisticas_voluntarios",
            )
    except PermissionError as erro:
        st.error(str(erro))
        return

    st.subheader("Relatórios de voluntários")

    periodo = _selecionar_periodo()

    if periodo is None:
        return

    inicio, fim = periodo

    try:
        indicadores = estatisticas_voluntarios(inicio, fim, ator_id=ator_id)
    except (ValueError, PermissionError) as erro:
        st.error(str(erro))
        return

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Voluntários cadastrados",
            indicadores["cadastrados"],
        )

    with col2:
        st.metric(
            "Voluntários ativos",
            indicadores["ativos"],
        )

    col3, col4 = st.columns(2)

    with col3:
        st.metric(
            "Participantes no período",
            indicadores["participantes"],
        )

    with col4:
        st.metric(
            "Presenças no período",
            indicadores["presencas"],
        )

    st.caption(
        f"Voluntários inativos: {indicadores['inativos']}. "
        "Os totais de cadastrados, ativos e inativos "
        "consideram a situação atual dos cadastros."
    )

    # Consulta pode visualizar somente os indicadores.
    if not tem_permissao(perfil, "relatorios_voluntarios"):
        st.info(
            "Os indicadores agregados estão disponíveis "
            "para consulta. Relatórios nominais são "
            "restritos à administração."
        )
        return

    try:
        ranking = ranking_voluntarios(inicio, fim, ator_id=ator_id)

        cadastros = relatorio_cadastros_voluntarios(inicio, fim, ator_id=ator_id)

    except (ValueError, PermissionError) as erro:
        st.error(str(erro))
        return

    st.divider()

    aba_ranking, aba_cadastros, aba_historico = st.tabs(
        [
            "Ranking",
            "Cadastrados",
            "Histórico individual",
        ]
    )

    with aba_ranking:
        st.write("#### Ranking de participação")

        st.caption(
            "Cada dia de presença vale um ponto. " "Empates recebem a mesma colocação."
        )

        if not ranking:
            st.info("Nenhuma participação registrada " "no período selecionado.")
        else:
            destaques = [r for r in ranking if r["posicao"] <= 3]
            tabela = [
                {
                    "Colocação": f"{r['posicao']}º",
                    "Voluntário": r["nome"],
                    "Presenças": r["presencas"],
                    "Situação": ("Ativo" if r["ativo"] else "Inativo"),
                }
                for r in ranking
            ]

            st.dataframe(
                tabela,
                hide_index=True,
                width="stretch",
            )

            if tem_permissao(perfil, "exportar_relatorios_voluntarios"):
                conteudo_csv = gerar_csv_ranking_voluntarios(ranking)

                st.download_button(
                    "Baixar ranking (CSV)",
                    data=conteudo_csv,
                    file_name=(f"prestserv_ranking_voluntarios_" f"{inicio}_{fim}.csv"),
                    mime="text/csv",
                    width="stretch",
                    key="baixar_ranking_voluntarios_csv",
                    on_click=registrar_download_csv_voluntarios,
                    args=(
                        ator_id,
                        "ranking",
                        inicio,
                        fim,
                        len(ranking),
                    ),
                )

            if tem_permissao(perfil, "exportar_relatorios_voluntarios"):
                try:
                    conteudo_pdf = gerar_pdf_ranking_voluntarios(
                        inicio,
                        fim,
                        ator_id=ator_id,
                    )
                except (ValueError, PermissionError) as erro:
                    st.error(str(erro))
                else:
                    st.download_button(
                        "Baixar ranking (PDF)",
                        data=conteudo_pdf,
                        file_name=(
                            f"prestserv_ranking_voluntarios_" f"{inicio}_{fim}.pdf"
                        ),
                        mime="application/pdf",
                        width="stretch",
                        key="baixar_ranking_voluntarios_pdf",
                        on_click=registrar_download_pdf_voluntarios,
                        args=(
                            ator_id,
                            "ranking",
                            inicio,
                            fim,
                            len(ranking),
                        ),
                    )

            if tem_permissao(
                perfil,
                "gerar_certificados_voluntarios",
            ):
                try:
                    conteudo_certificados = gerar_certificados_voluntarios(
                        inicio,
                        fim,
                        ator_id=ator_id,
                    )

                except (ValueError, PermissionError) as erro:
                    st.error(str(erro))

                else:
                    st.divider()

                    st.write("#### Certificados de reconhecimento")

                    st.caption(
                        f"Serão gerados {len(destaques)} "
                        "certificado(s), um por página, "
                        "respeitando os empates nas três "
                        "primeiras colocações."
                    )

                    st.download_button(
                        "Baixar certificados (PDF)",
                        data=conteudo_certificados,
                        file_name=(
                            f"prestserv_certificados_voluntarios_" f"{inicio}_{fim}.pdf"
                        ),
                        mime="application/pdf",
                        width="stretch",
                        key=(f"baixar_certificados_voluntarios_" f"{inicio}_{fim}"),
                        on_click=(registrar_download_certificados_voluntarios),
                        args=(
                            ator_id,
                            inicio,
                            fim,
                        ),
                    )

            destaques = [r for r in ranking if r["posicao"] <= 3]

            st.caption(
                f"{len(destaques)} voluntário(s) nas "
                "três primeiras colocações, "
                "considerando os empates."
            )

    with aba_cadastros:
        st.write("#### Relação de voluntários cadastrados")

        if not cadastros:
            st.info("Nenhum voluntário cadastrado.")
        else:
            tabela = [
                {
                    "ID": r["voluntario_id"],
                    "Voluntário": r["nome"],
                    "Telefone": r["telefone"] or "",
                    "Situação": ("Ativo" if r["ativo"] else "Inativo"),
                    "Cadastro": r["criado_em"][:10],
                    "No período": r["presencas_periodo"],
                    "Total": r["presencas_total"],
                    "Última presença": (r["ultima_participacao"] or "Nunca"),
                }
                for r in cadastros
            ]

            st.dataframe(
                tabela,
                hide_index=True,
                width="stretch",
            )

            if tem_permissao(perfil, "exportar_relatorios_voluntarios"):
                conteudo_csv = gerar_csv_cadastros_voluntarios(cadastros)

                st.download_button(
                    "Baixar voluntários cadastrados (CSV)",
                    data=conteudo_csv,
                    file_name=(
                        f"prestserv_voluntarios_cadastrados_" f"{inicio}_{fim}.csv"
                    ),
                    mime="text/csv",
                    width="stretch",
                    key="baixar_cadastros_voluntarios_csv",
                    on_click=registrar_download_csv_voluntarios,
                    args=(
                        ator_id,
                        "cadastros",
                        inicio,
                        fim,
                        len(cadastros),
                    ),
                )

            if tem_permissao(
                perfil,
                "exportar_relatorios_voluntarios",
            ):
                try:
                    conteudo_pdf = gerar_pdf_cadastros_voluntarios(
                        inicio,
                        fim,
                        ator_id=ator_id,
                    )

                except (ValueError, PermissionError) as erro:
                    st.error(str(erro))

                else:
                    st.download_button(
                        "Baixar voluntários cadastrados (PDF)",
                        data=conteudo_pdf,
                        file_name=(
                            f"prestserv_voluntarios_cadastrados_" f"{inicio}_{fim}.pdf"
                        ),
                        mime="application/pdf",
                        width="stretch",
                        key="baixar_cadastros_voluntarios_pdf",
                        on_click=registrar_download_pdf_voluntarios,
                        args=(
                            ator_id,
                            "cadastros",
                            inicio,
                            fim,
                            len(cadastros),
                        ),
                    )

    with aba_historico:
        st.write("#### Histórico individual")

        if not cadastros:
            st.info("Nenhum voluntário cadastrado.")
        else:
            opcoes = {
                r["voluntario_id"]: (
                    r["nome"] + (" [Inativo]" if not r["ativo"] else "")
                )
                for r in cadastros
            }

            voluntario_id = st.selectbox(
                "Selecione o voluntário",
                options=list(opcoes),
                format_func=lambda vid: opcoes[vid],
                index=None,
                placeholder="Digite ou selecione um nome...",
                key="historico_relatorio_voluntario",
            )

            if voluntario_id is not None:
                try:
                    historico = historico_presencas_voluntario(
                        voluntario_id,
                        inicio,
                        fim,
                        ator_id=ator_id,
                    )
                except (ValueError, PermissionError) as erro:
                    st.error(str(erro))
                    return

                st.metric(
                    "Presenças no período",
                    len(historico),
                )

                if not historico:
                    st.info(
                        "Este voluntário não possui presenças "
                        "no período selecionado."
                    )
                else:
                    tabela = [
                        {
                            "Data": r["data"],
                            "Registrado em": r["criado_em"],
                            "Operador": r["registrado_por"],
                        }
                        for r in historico
                    ]

                    st.dataframe(
                        tabela,
                        hide_index=True,
                        width="stretch",
                    )

                    if tem_permissao(
                        perfil,
                        "exportar_relatorios_voluntarios",
                    ):
                        conteudo_csv = gerar_csv_historico_voluntario(historico)

                        st.download_button(
                            "Baixar histórico individual (CSV)",
                            data=conteudo_csv,
                            file_name=(
                                f"prestserv_historico_voluntario_"
                                f"{voluntario_id}_{inicio}_{fim}.csv"
                            ),
                            mime="text/csv",
                            width="stretch",
                            key=(
                                f"baixar_historico_voluntario_csv_"
                                f"{voluntario_id}_{inicio}_{fim}"
                            ),
                            on_click=registrar_download_csv_voluntarios,
                            args=(
                                ator_id,
                                "historico",
                                inicio,
                                fim,
                                len(historico),
                                voluntario_id,
                            ),
                        )

                if tem_permissao(
                    perfil,
                    "exportar_relatorios_voluntarios",
                ):
                    try:
                        conteudo_pdf = gerar_pdf_historico_voluntario(
                            voluntario_id,
                            inicio,
                            fim,
                            ator_id=ator_id,
                        )

                    except (ValueError, PermissionError) as erro:
                        st.error(str(erro))

                    else:
                        st.download_button(
                            "Baixar histórico individual (PDF)",
                            data=conteudo_pdf,
                            file_name=(
                                f"prestserv_historico_voluntario_"
                                f"{voluntario_id}_{inicio}_{fim}.pdf"
                            ),
                            mime="application/pdf",
                            width="stretch",
                            key=(
                                f"baixar_historico_voluntario_pdf_"
                                f"{voluntario_id}_{inicio}_{fim}"
                            ),
                            on_click=registrar_download_pdf_voluntarios,
                            args=(
                                ator_id,
                                "historico",
                                inicio,
                                fim,
                                len(historico),
                                voluntario_id,
                            ),
                        )


def gerar_csv_cadastros_voluntarios(cadastros):
    """Gera o CSV da relação de voluntários cadastrados."""

    saida = StringIO(newline="")

    escritor = csv.writer(
        saida,
        delimiter=";",
        lineterminator="\r\n",
    )

    escritor.writerow(
        [
            "ID",
            "Voluntário",
            "Telefone",
            "Situação",
            "Data de cadastro",
            "Presenças no período",
            "Presenças totais",
            "Última participação",
        ]
    )

    for registro in cadastros:
        escritor.writerow(
            [
                registro["voluntario_id"],
                _texto_csv_seguro(registro["nome"]),
                _texto_csv_seguro(registro["telefone"]),
                "Ativo" if registro["ativo"] else "Inativo",
                registro["criado_em"][:10],
                registro["presencas_periodo"],
                registro["presencas_total"],
                registro["ultima_participacao"] or "Nunca",
            ]
        )

    return saida.getvalue().encode("utf-8-sig")


def gerar_csv_historico_voluntario(historico):
    """Gera o CSV do histórico individual de presenças."""

    saida = StringIO(newline="")

    escritor = csv.writer(
        saida,
        delimiter=";",
        lineterminator="\r\n",
    )

    escritor.writerow(
        [
            "Data",
            "Registrado em",
            "Operador",
        ]
    )

    for registro in historico:
        escritor.writerow(
            [
                registro["data"],
                registro["criado_em"],
                _texto_csv_seguro(registro["registrado_por"]),
            ]
        )

    return saida.getvalue().encode("utf-8-sig")


def registrar_download_pdf_voluntarios(
    ator_id, tipo, inicio, fim, total_linhas, voluntario_id=None
):
    """Audita downloads PDF dos relatórios de voluntários."""

    if tipo not in {"ranking", "cadastros", "historico"}:
        raise ValueError("Tipo de relatório inválido.")

    if tipo == "historico":
        if type(voluntario_id) is not int or voluntario_id <= 0:
            raise ValueError("Identificador de voluntário inválido.")
    elif voluntario_id is not None:
        raise ValueError("Identificador não permitido neste relatório.")

    if type(total_linhas) is not int or total_linhas < 0:
        raise ValueError("Quantidade de registros inválida.")

    try:
        data_inicio = date.fromisoformat(inicio)
        data_fim = date.fromisoformat(fim)

        if (
            inicio != data_inicio.isoformat()
            or fim != data_fim.isoformat()
            or data_inicio > data_fim
        ):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Período inválido.") from None

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(
            conexao,
            ator_id,
            "exportar_relatorios_voluntarios",
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        detalhes = {
            "tipo": tipo,
            "inicio": inicio,
            "fim": fim,
            "total_linhas": total_linhas,
        }

        if tipo == "historico":
            detalhes["voluntario_id"] = voluntario_id

        registrar_log(
            conexao,
            acao="exportar_relatorio_voluntarios_pdf",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="voluntarios",
            detalhes=detalhes,
        )


def registrar_download_certificados_voluntarios(ator_id, inicio, fim):
    """Audita a solicitação de download dos certificados."""

    # A permissão de emissão é específica.
    with conectar() as conexao:
        exigir_permissao_usuario(
            conexao,
            ator_id,
            "gerar_certificados_voluntarios",
        )

    # Consulta novamente os classificados para
    # registrar quem foi contemplado.
    destaques = destaques_voluntarios(
        inicio,
        fim,
        ator_id=ator_id,
    )

    if not destaques:
        raise ValueError("Não há voluntários classificados " "no período selecionado.")

    certificados = [
        {
            "voluntario_id": registro["voluntario_id"],
            "posicao": registro["posicao"],
            "presencas": registro["presencas"],
        }
        for registro in destaques
    ]

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(
            conexao,
            ator_id,
            "gerar_certificados_voluntarios",
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao="exportar_certificados_voluntarios_pdf",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="voluntarios",
            detalhes={
                "inicio": inicio,
                "fim": fim,
                "total_certificados": len(certificados),
                "certificados": certificados,
            },
        )
