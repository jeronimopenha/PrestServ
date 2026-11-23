import sqlite3
import streamlit as st

from auth import (
    autenticar,
    criar_usuario,
    listar_usuarios,
    atualizar_usuario,
    definir_status_usuario,
    redefinir_senha,
    excluir_usuario,
)
from database import conectar, registrar_log
from presencas import tela_presencas
from cadastros import tela_cadastros
from relatorios import tela_relatorios
from inicializar_banco import inicializar_banco
from tela_backups import tela_backups
from estrutura_v110 import consultar_vinculos
from tela_logs import tela_logs
from tela_entradas import tela_entradas
from tela_cadastros_voluntarios import tela_cadastros_voluntarios
from tela_presencas_voluntarios import tela_presencas_voluntarios
from tela_relatorios_voluntarios import tela_relatorios_voluntarios
from permissoes import PERFIS, tem_permissao
from common import BASIC_TITTLE, VERSAO, ANO

st.set_page_config(page_title=BASIC_TITTLE, page_icon="🏠", layout="centered")

st.markdown(
    """
<style>
.st-key-creditos_prestserv {
    position: fixed;
    bottom: 15px;
    left: 15px;
    width: 260px;
    padding-top: 12px;
    border-top: 1px solid #555555;
    background-color: var(--secondary-background-color);
    z-index: 100;
}
</style>
""",
    unsafe_allow_html=True,
)


def usuario_atual():
    """Valida a sessão consultando o banco novamente."""
    usuario = st.session_state.get("usuario")

    if not usuario:
        return None

    with conectar() as conexao:
        registro = conexao.execute(
            """
            SELECT id, nome, login, perfil
            FROM usuarios
            WHERE id = ? AND ativo = 1
            """,
            (usuario["id"],),
        ).fetchone()

    if registro is None:
        st.session_state.pop("usuario", None)
        return None

    return dict(registro)


def tela_login():
    st.title(BASIC_TITTLE)

    with st.form("login"):
        login = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button(
            "Entrar",
            width="stretch",
        )

    if entrar:
        usuario = autenticar(login, senha)

        if usuario:
            st.session_state["usuario"] = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


def painel_admin():
    ator = usuario_atual()

    if ator is None or not tem_permissao(ator["perfil"], "gerenciar_usuarios"):
        st.error("Você não tem permissão para administrar usuários.")
        return

    st.subheader("Administração de usuários")

    aba_usuarios, aba_novo = st.tabs(["Gerenciar usuários", "Novo usuário"])

    with aba_usuarios:
        usuarios = listar_usuarios(ator["id"])

        if not usuarios:
            st.info("Nenhum usuário cadastrado.")
        else:
            opcoes = {
                u["id"]: (
                    f"{u['nome']} ({u['login']})"
                    + (" [Inativo]" if not u["ativo"] else "")
                )
                for u in usuarios
            }

            usuario_id = st.selectbox(
                "Selecione o usuário",
                options=list(opcoes.keys()),
                format_func=lambda id: opcoes[id],
                index=None,
                placeholder="Selecione um usuário...",
            )

            if usuario_id is not None:
                usuario = next(u for u in usuarios if u["id"] == usuario_id)

                with st.form(f"editar_usuario_{usuario_id}"):
                    nome = st.text_input("Nome", value=usuario["nome"])

                    login = st.text_input("Login", value=usuario["login"])

                    opcoes_perfis = list(PERFIS.keys())

                    perfil = st.selectbox(
                        "Perfil",
                        options=opcoes_perfis,
                        index=opcoes_perfis.index(usuario["perfil"]),
                        format_func=lambda p: PERFIS[p],
                    )

                    salvar = st.form_submit_button(
                        "Salvar alterações",
                        type="primary",
                        width="stretch",
                    )

                if salvar:
                    try:
                        atualizar_usuario(
                            usuario_id, nome, login, perfil, usuario_atual()["id"]
                        )
                        st.toast("Usuário atualizado!")
                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error("Esse login já está em uso.")

                    except ValueError as erro:
                        st.error(str(erro))

                st.divider()

                st.write("### Situação da conta")

                if usuario["ativo"]:
                    st.success("Conta ativa")

                    if st.button(
                        "Desativar usuário", key=f"desativar_usuario_{usuario_id}"
                    ):
                        try:
                            definir_status_usuario(
                                usuario_id, False, usuario_atual()["id"]
                            )
                            st.rerun()
                        except ValueError as erro:
                            st.error(str(erro))
                else:
                    st.warning("Conta inativa")

                    if st.button(
                        "Reativar usuário", key=f"reativar_usuario_{usuario_id}"
                    ):
                        definir_status_usuario(usuario_id, True, usuario_atual()["id"])
                        st.rerun()

                st.divider()

                st.write("### Redefinir senha")

                with st.form(f"senha_usuario_{usuario_id}"):
                    nova_senha = st.text_input("Nova senha", type="password")

                    confirmar_senha = st.text_input(
                        "Confirmar nova senha", type="password"
                    )

                    redefinir = st.form_submit_button(
                        "Redefinir senha",
                        width="stretch",
                    )

                if redefinir:
                    if nova_senha != confirmar_senha:
                        st.error("As senhas não coincidem.")
                    else:
                        try:
                            redefinir_senha(
                                usuario_id,
                                nova_senha,
                                usuario_atual()["id"],
                            )
                            st.success("Senha redefinida!")
                        except ValueError as erro:
                            st.error(str(erro))

                st.divider()
                st.write("### Excluir usuário")

                ator = usuario_atual()

                with conectar() as conexao:
                    vinculos = consultar_vinculos(conexao, "usuarios", usuario_id)

                    total_superadmins = conexao.execute("""
                        SELECT COUNT(*)
                        FROM usuarios
                        WHERE perfil = 'superadmin'
                        AND ativo = 1
                        """).fetchone()[0]

                # Identifica os motivos que impedem a exclusão.
                impedimentos = []

                if ator is None or usuario_id == ator["id"]:
                    impedimentos.append("Você não pode excluir sua própria conta.")

                if (
                    usuario["perfil"] == "superadmin"
                    and usuario["ativo"]
                    and total_superadmins <= 1
                ):
                    impedimentos.append(
                        "O último superadministrador ativo não pode ser excluído."
                    )

                if vinculos:
                    impedimentos.append(
                        "Este usuário possui relacionamentos " "com outras tabelas."
                    )

                pode_excluir = not impedimentos

                if pode_excluir:
                    st.success("Este usuário pode ser excluído definitivamente.")
                else:
                    for motivo in impedimentos:
                        st.warning(motivo)

                    for vinculo in vinculos:
                        st.caption(
                            f"{vinculo['tabela']}: "
                            f"{vinculo['quantidade']} registro(s)"
                        )

                confirmar = st.checkbox(
                    "Confirmo que desejo excluir " "definitivamente este usuário.",
                    disabled=not pode_excluir,
                    key=f"confirmar_exclusao_usuario_{usuario_id}",
                )

                if st.button(
                    "Excluir usuário",
                    disabled=not pode_excluir or not confirmar,
                    key=f"excluir_usuario_{usuario_id}",
                    type="secondary",
                ):
                    try:
                        excluir_usuario(
                            usuario_id,
                            ator_id=ator["id"],
                        )

                        st.toast("Usuário excluído com sucesso!")
                        st.rerun()

                    except ValueError as erro:
                        st.error(str(erro))
                    except sqlite3.IntegrityError:
                        st.error(
                            "A exclusão foi bloqueada "
                            "por um relacionamento no banco."
                        )

    with aba_novo:
        with st.form("novo_usuario", clear_on_submit=True):
            nome = st.text_input("Nome completo")
            login = st.text_input("Login")
            senha = st.text_input("Senha inicial", type="password")
            opcoes_perfis = list(PERFIS.keys())

            perfil = st.selectbox(
                "Perfil",
                options=opcoes_perfis,
                index=opcoes_perfis.index("porteiro"),
                format_func=lambda p: PERFIS[p],
            )

            salvar = st.form_submit_button(
                "Cadastrar usuário",
                width="stretch",
            )

        if salvar:
            try:
                ator = usuario_atual()
                criar_usuario(
                    nome,
                    login,
                    senha,
                    perfil,
                    ator_id=ator["id"],
                    ator_login=ator["login"],
                )
                st.success("Usuário cadastrado com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Esse login já está cadastrado.")
            except ValueError as erro:
                st.error(str(erro))


def painel_porteiro():
    tela_presencas()


def montar_menu(perfil):
    """Organiza as páginas disponíveis para cada perfil."""

    if perfil in ("superadmin", "admin"):
        menu = {
            "Atendimentos": [
                "Presenças",
                "Cadastros",
                "Entradas",
                "Relatórios",
            ],
            "Voluntários": [
                "Presenças de voluntários",
                "Cadastro de voluntários",
                "Relatórios de voluntários",
            ],
        }

        administracao = []

        if tem_permissao(perfil, "consultar_logs"):
            administracao.append("Logs do sistema")

        if tem_permissao(perfil, "gerar_backup") and tem_permissao(
            perfil, "restaurar_backup"
        ):
            administracao.append("Backup e restauração")

        if tem_permissao(perfil, "gerenciar_usuarios"):
            administracao.append("Administração")

        if administracao:
            menu["Administração"] = administracao

        return menu

    if perfil == "porteiro":
        return {
            "Atendimentos": [
                "Presenças",
            ],
            "Voluntários": [
                "Presenças de voluntários",
            ],
        }

    if perfil == "consulta":
        return {
            "Atendimentos": [
                "Relatórios",
            ],
            "Voluntários": [
                "Relatórios de voluntários",
            ],
        }

    if perfil == "secretaria":
        return {
            "Atendimentos": [
                "Cadastros",
                "Entradas",
            ],
            "Voluntários": [
                "Cadastro de voluntários",
            ],
        }

    return {}


def main():
    inicializar_banco()
    usuario = usuario_atual()

    if usuario is None:
        tela_login()
        return

    with st.sidebar:
        st.write(f"**{usuario['nome']}**")
        st.caption(f"Perfil: {PERFIS.get(usuario['perfil'], 'Desconhecido')}")

        if st.button(
            "Sair",
            width="stretch",
        ):
            with conectar() as conexao:
                registrar_log(
                    conexao,
                    acao="logout",
                    usuario_id=usuario["id"],
                    usuario_login=usuario["login"],
                    entidade="usuarios",
                    entidade_id=usuario["id"],
                )
            st.session_state.clear()
            st.rerun()

    st.title(BASIC_TITTLE)

    perfil = usuario["perfil"]

    # Organização das áreas e páginas.
    menu = montar_menu(perfil)

    if not menu:
        st.error("Perfil de usuário inválido.")
        return

    if perfil == "porteiro":
        # Navegação direta, sem seleção de área.
        pagina = st.sidebar.radio(
            "Navegação",
            [
                "Presenças",
                "Presenças de voluntários",
            ],
            key="navegacao_porteiro",
        )

    else:
        # Navegação organizada por áreas
        # para os demais perfis.
        area = st.sidebar.selectbox(
            "Área",
            options=list(menu),
            key=f"navegacao_area_{perfil}",
        )

        pagina = st.sidebar.radio(
            "Página",
            options=menu[area],
            key=f"navegacao_pagina_{perfil}_{area}",
        )

    # Associação entre páginas e suas funções.
    telas = {
        "Presenças": tela_presencas,
        "Cadastros": tela_cadastros,
        "Entradas": tela_entradas,
        "Relatórios": tela_relatorios,
        "Presenças de voluntários": tela_presencas_voluntarios,
        "Cadastro de voluntários": tela_cadastros_voluntarios,
        "Relatórios de voluntários": tela_relatorios_voluntarios,
        "Logs do sistema": tela_logs,
        "Backup e restauração": tela_backups,
        "Administração": painel_admin,
    }

    telas[pagina]()

    with st.sidebar:
        with st.container(key="creditos_prestserv"):
            st.caption(f"PrestServ {VERSAO}")
            st.caption("Desenvolvido por Jeronimo Costa Penha")
            st.caption(f"© {ANO}")


if __name__ == "__main__":
    main()
