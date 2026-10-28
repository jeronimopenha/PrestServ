import getpass
import sqlite3

from auth import criar_usuario, TAM_SENHA
from database import conectar


def main():
    with conectar() as conexao:
        total = conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

    if total > 0:
        print("Já existem usuários cadastrados.")
        print("A criação inicial está desabilitada.")
        return

    print("=== Primeiro administrador do PrestServ ===")

    nome = input("Nome: ").strip()
    login = input("Login: ").strip()
    senha = getpass.getpass(f"Senha (mínimo {TAM_SENHA} caracteres): ")
    confirmacao = getpass.getpass("Confirme a senha: ")

    if senha != confirmacao:
        print("As senhas não coincidem.")
        return

    try:
        criar_usuario(nome, login, senha, "admin")
        print("Administrador criado com sucesso!")
    except (ValueError, sqlite3.IntegrityError) as erro:
        print(f"Erro: {erro}")


if __name__ == "__main__":
    main()
