"""Interface de registro e manutenção das entradas de doações e compras.

Não realiza controle de estoque. Usa exclusivamente as operações autorizadas
pelo módulo entradas.py.
"""

from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
import re

import pandas as pd
import streamlit as st

from database import conectar, data_atual
from entradas import (
    atualizar_entrada,
    excluir_entrada,
    listar_entradas,
    registrar_entrada,
)
from permissoes import exigir_permissao_usuario


TIPOS = {"doacao": "Doação", "compra": "Compra"}


def _para_centavos(texto):
    """Aceita 85,90 ou 85.90, sem separador de milhares; vazio = NULL."""
    if not isinstance(texto, str):
        raise ValueError("Valor monetário inválido.")

    texto = texto.strip()
    if not texto:
        return None

    if not re.fullmatch(r"\d+(?:[,.]\d{1,2})?", texto):
        raise ValueError(
            "Valor inválido. Use, por exemplo, 85,90 (sem R$ ou separador de milhares)."
        )

    centavos = int(Decimal(texto.replace(",", ".")) * 100)
    if centavos > 999_999_999_999:
        raise ValueError("O valor informado ultrapassa o limite permitido.")
    return centavos


def _centavos_para_campo(valor):
    if valor is None:
        return ""
    return f"{valor // 100},{valor % 100:02d}"


def _centavos_para_exibicao(valor):
    if valor is None:
        return "—"
    numero = Decimal(valor) / 100
    return f"R$ {numero:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def _campos_formulario(prefixo, registro=None):
    """Desenha os campos compartilhados pelos formulários de inclusão e edição."""
    registro = registro or {}
    hoje = date.fromisoformat(data_atual())
    valor_data = date.fromisoformat(registro["data"]) if registro else hoje

    data = st.date_input(
        "Data da entrada",
        value=valor_data,
        max_value=hoje,
        format="DD/MM/YYYY",
        key=f"{prefixo}_data",
    )

    c1, c2 = st.columns(2)
    with c1:
        tipo = st.selectbox(
            "Tipo *",
            options=list(TIPOS),
            index=list(TIPOS).index(registro.get("tipo", "doacao")),
            format_func=lambda x: TIPOS[x],
            key=f"{prefixo}_tipo",
        )
    with c2:
        categoria = st.text_input(
            "Categoria *",
            value=registro.get("categoria") or "",
            placeholder="Ex.: Alimentos, Higiene, Vestuário",
            key=f"{prefixo}_categoria",
        )

    item = st.text_input(
        "Item *",
        value=registro.get("item") or "",
        placeholder="Ex.: Arroz, Sabonete, Cobertor",
        key=f"{prefixo}_item",
    )

    c3, c4 = st.columns(2)
    with c3:
        quantidade = st.number_input(
            "Quantidade *",
            min_value=0.001,
            value=float(registro.get("quantidade", 1.0)),
            step=0.5,
            format="%.3f",
            key=f"{prefixo}_quantidade",
        )
    with c4:
        unidade = st.text_input(
            "Unidade *",
            value=registro.get("unidade") or "un",
            placeholder="Ex.: un, kg, g, L, pacote",
            key=f"{prefixo}_unidade",
        )

    origem = st.text_input(
        "Origem (doador ou fornecedor) — opcional",
        value=registro.get("origem") or "",
        key=f"{prefixo}_origem",
    )
    valor_texto = st.text_input(
        "Valor total (R$) — opcional",
        value=_centavos_para_campo(registro.get("valor_centavos")),
        placeholder="Ex.: 85,90 (sem separador de milhares)",
        help="Deixe vazio quando o valor não for conhecido. Não use R$ nem pontos de milhar.",
        key=f"{prefixo}_valor",
    )

    return {
        "data": data.isoformat(),
        "tipo": tipo,
        "categoria": categoria,
        "item": item,
        "quantidade": quantidade,
        "unidade": unidade,
        "origem": origem,
        "valor_texto": valor_texto,
    }


def _argumentos_entrada(campos):
    """Converte dados da interface para a assinatura do módulo entradas.py."""
    return {
        "data": campos["data"],
        "tipo": campos["tipo"],
        "categoria": campos["categoria"],
        "item": campos["item"],
        "quantidade": campos["quantidade"],
        "unidade": campos["unidade"],
        "origem": campos["origem"],
        "valor_centavos": _para_centavos(campos["valor_texto"]),
    }


def _tabela(registros):
    return pd.DataFrame(
        [
            {
                "ID": r["id"],
                "Data": date.fromisoformat(r["data"]).strftime("%d/%m/%Y"),
                "Tipo": TIPOS[r["tipo"]],
                "Categoria": r["categoria"],
                "Item": r["item"],
                "Quantidade": r["quantidade"],
                "Unidade": r["unidade"],
                "Origem": r["origem"] or "",
                "Valor total": _centavos_para_exibicao(r["valor_centavos"]),
                "Registrado por": r["registrado_por"],
            }
            for r in registros
        ]
    )


def tela_entradas():
    ator = st.session_state["usuario"]
    ator_id = ator["id"]

    # O menu não substitui a autorização no banco.
    with conectar() as conexao:
        exigir_permissao_usuario(conexao, ator_id, "gerenciar_entradas")

    st.subheader("Entradas — Doações e Compras")
    st.caption("Histórico de recebimentos e aquisições, sem controle de estoque.")

    aba_registrar, aba_consultar = st.tabs(["Registrar entrada", "Consultar / editar"])

    with aba_registrar:
        with st.form("form_registrar_entrada", clear_on_submit=True):
            campos = _campos_formulario("nova_entrada")
            salvar = st.form_submit_button(
                "Registrar entrada", type="primary", width="stretch"
            )

        if salvar:
            try:
                nova_id = registrar_entrada(
                    **_argumentos_entrada(campos), ator_id=ator_id
                )
            except (ValueError, PermissionError) as erro:
                st.error(str(erro))
            else:
                st.success(f"Entrada #{nova_id} registrada com sucesso!")

    with aba_consultar:
        periodo = st.selectbox(
            "Período",
            ["Mês atual", "Últimos 90 dias", "Todo o histórico", "Personalizado"],
            key="entradas_periodo",
        )
        hoje = date.fromisoformat(data_atual())
        if periodo == "Mês atual":
            inicio, fim = hoje.replace(day=1), hoje
        elif periodo == "Últimos 90 dias":
            inicio, fim = hoje - timedelta(days=89), hoje
        elif periodo == "Todo o histórico":
            inicio = fim = None
        else:
            c1, c2 = st.columns(2)
            with c1:
                inicio = st.date_input(
                    "Data inicial", value=hoje.replace(day=1),
                    max_value=hoje, format="DD/MM/YYYY", key="entradas_data_inicio"
                )
            with c2:
                fim = st.date_input(
                    "Data final", value=hoje,
                    max_value=hoje, format="DD/MM/YYYY", key="entradas_data_fim"
                )

        c3, c4 = st.columns(2)
        with c3:
            tipo_exibicao = st.selectbox(
                "Tipo", ["Todos", "Doações", "Compras"], key="entradas_filtro_tipo"
            )
        with c4:
            categoria = st.text_input(
                "Categoria (nome exato, opcional)",
                placeholder="Ex.: Alimentos",
                key="entradas_filtro_categoria",
            ).strip()

        if inicio is not None and fim is not None and inicio > fim:
            st.error("A data inicial não pode superar a data final.")
            return

        tipo_filtro = {"Todos": None, "Doações": "doacao", "Compras": "compra"}[
            tipo_exibicao
        ]
        try:
            registros = listar_entradas(
                inicio=inicio.isoformat() if inicio is not None else None,
                fim=fim.isoformat() if fim is not None else None,
                tipo=tipo_filtro,
                categoria=categoria or None,
                ator_id=ator_id,
            )
        except (ValueError, PermissionError) as erro:
            st.error(str(erro))
            return

        st.metric("Entradas encontradas", len(registros))
        if not registros:
            st.info("Nenhuma entrada encontrada com os filtros escolhidos.")
            return

        st.caption("Selecione uma linha para editar ou excluir o lançamento.")
        assinatura = sha256(
            repr(tuple((r["id"], r["data"], r["item"], r["quantidade"],
                        r["valor_centavos"]) for r in registros)).encode("utf-8")
        ).hexdigest()[:16]

        evento = st.dataframe(
            _tabela(registros),
            hide_index=True,
            width="stretch",
            height=40 + 35 * min(7, len(registros)),
            row_height=35,
            on_select="rerun",
            selection_mode="single-row",
            key=f"grade_entradas_{assinatura}",
        )
        linhas = evento.selection.rows
        if not linhas:
            return

        registro = registros[linhas[0]]
        entrada_id = registro["id"]
        st.divider()
        st.write(f"### Editar entrada #{entrada_id}")

        revisao = st.session_state.get("entradas_revisao_form", 0)
        prefixo = f"editar_entrada_{entrada_id}_{revisao}"
        with st.form(f"form_{prefixo}"):
            campos_edicao = _campos_formulario(prefixo, registro)
            atualizar = st.form_submit_button(
                "Salvar alterações", type="primary", width="stretch"
            )

        if atualizar:
            try:
                alterou = atualizar_entrada(
                    entrada_id,
                    **_argumentos_entrada(campos_edicao),
                    ator_id=ator_id,
                )
            except (ValueError, PermissionError) as erro:
                st.error(str(erro))
            else:
                if alterou:
                    st.session_state["entradas_revisao_form"] = revisao + 1
                    st.toast("Entrada atualizada com sucesso!")
                    st.rerun()
                else:
                    st.info("Nenhuma alteração identificada.")

        with st.expander("Excluir esta entrada definitivamente"):
            confirmar = st.checkbox(
                f"Confirmo a exclusão definitiva da entrada #{entrada_id}.",
                key=f"confirmar_exclusao_entrada_{entrada_id}_{revisao}",
            )
            if st.button(
                "Excluir entrada",
                type="secondary",
                disabled=not confirmar,
                key=f"excluir_entrada_{entrada_id}_{revisao}",
            ):
                try:
                    excluir_entrada(entrada_id, ator_id=ator_id)
                except (ValueError, PermissionError) as erro:
                    st.error(str(erro))
                else:
                    st.session_state["entradas_revisao_form"] = revisao + 1
                    st.toast("Entrada excluída. A operação foi registrada nos logs.")
                    st.rerun()
