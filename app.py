import sqlite3
import streamlit as st

from auth import (
    autenticar,
    criar_usuario,
    listar_usuarios,
    atualizar_usuario,
    definir_status_usuario,
    redefinir_senha,
)
from database import conectar
from presencas import tela_presencas
from cadastros import tela_cadastros
from relatorios import tela_relatorios
from inicializar_banco import inicializar_banco
from tela_backups import tela_backups
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
    background-color: #2b2b33;
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
        entrar = st.form_submit_button("Entrar", use_container_width=True)

    if entrar:
        usuario = autenticar(login, senha)

        if usuario:
            st.session_state["usuario"] = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


def painel_admin():
    st.subheader("Administração de usuários")

    aba_usuarios, aba_novo = st.tabs(["Gerenciar usuários", "Novo usuário"])

    with aba_usuarios:
        usuarios = listar_usuarios()

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

                    perfil = st.selectbox(
                        "Perfil",
                        ["porteiro", "admin"],
                        index=(1 if usuario["perfil"] == "admin" else 0),
                    )

                    salvar = st.form_submit_button(
                        "Salvar alterações", type="primary", use_container_width=True
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
                        "Redefinir senha", use_container_width=True
                    )

                if redefinir:
                    if nova_senha != confirmar_senha:
                        st.error("As senhas não coincidem.")
                    else:
                        try:
                            redefinir_senha(usuario_id, nova_senha)
                            st.success("Senha redefinida!")
                        except ValueError as erro:
                            st.error(str(erro))

    with aba_novo:
        with st.form("novo_usuario", clear_on_submit=True):
            nome = st.text_input("Nome completo")
            login = st.text_input("Login")
            senha = st.text_input("Senha inicial", type="password")
            perfil = st.selectbox("Perfil", ["porteiro", "admin"])

            salvar = st.form_submit_button(
                "Cadastrar usuário", use_container_width=True
            )

        if salvar:
            try:
                criar_usuario(nome, login, senha, perfil)
                st.success("Usuário cadastrado com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Esse login já está cadastrado.")
            except ValueError as erro:
                st.error(str(erro))


def painel_porteiro():
    tela_presencas()


def main():
    inicializar_banco()
    usuario = usuario_atual()

    if usuario is None:
        tela_login()
        return

    with st.sidebar:
        st.write(f"**{usuario['nome']}**")
        st.caption(f"Perfil: {usuario['perfil']}")

        if st.button("Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.title(BASIC_TITTLE)

    if usuario["perfil"] == "admin":
        pagina = st.sidebar.radio(
            "Navegação",
            [
                "Presenças",
                "Cadastros",
                "Relatórios",
                "Backup e restauração",
                "Administração",
            ],
        )

        if pagina == "Presenças":
            tela_presencas()
        elif pagina == "Cadastros":
            tela_cadastros()
        elif pagina == "Relatórios":
            tela_relatorios()
        elif pagina == "Backup e restauração":
            tela_backups()
        else:
            painel_admin()

    elif usuario["perfil"] == "porteiro":
        tela_presencas()

    else:
        st.error("Perfil de usuário inválido.")

    with st.sidebar:
        with st.container(key="creditos_prestserv"):
            st.caption(f"PrestServ {VERSAO}")
            st.caption("Desenvolvido por Jeronimo Costa Penha")
            st.caption(f"© {ANO}")


if __name__ == "__main__":
    main()
