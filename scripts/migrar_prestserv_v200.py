#!/usr/bin/env python3
"""Migra uma COPIA do SQLite PrestServ V1 (esquema 0/1) para V2.

A origem e aberta somente para leitura, via SQLite backup().
O arquivo de saida deve ser novo e nao sera sobrescrito.
Execute na raiz do projeto PrestServ, com o ambiente virtual ativo.
"""

import argparse
import os
from pathlib import Path
import sqlite3
import tempfile

from bd_schemes.estrutura_v110 import criar_estrutura_logs
from bd_schemes.estrutura_v200 import (
    migrar_usuarios_v200,
    promover_primeiro_superadmin,
)
from bd_schemes.estrutura_voluntarios import criar_estrutura_voluntarios
from bd_schemes.estrutura_entradas import criar_estrutura_entradas


TABELAS_PRESERVADAS = (
    "pessoas", "fotos_pessoas", "servicos", "presencas",
    "presenca_servicos", "usuarios",
)


def verificar_integridade(conexao, etapa):
    integridade = conexao.execute("PRAGMA integrity_check").fetchone()[0]
    if integridade != "ok":
        raise RuntimeError(f"{etapa}: integrity_check falhou: {integridade}")
    violacoes = conexao.execute("PRAGMA foreign_key_check").fetchall()
    if violacoes:
        raise RuntimeError(f"{etapa}: {len(violacoes)} violacao(oes) de FK")


def contar_registros(conexao):
    return {
        tabela: conexao.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()[0]
        for tabela in TABELAS_PRESERVADAS
    }


def migrar_copia(origem, saida, login_admin):
    origem = origem.expanduser().resolve(strict=True)
    saida = saida.expanduser().absolute()

    if not origem.is_file():
        raise ValueError("A origem deve ser um banco SQLite existente.")
    if origem == saida.resolve() or saida.exists() or saida.is_symlink():
        raise ValueError("A saida precisa ser um arquivo novo, diferente da origem.")
    if not saida.parent.is_dir():
        raise ValueError("A pasta de destino nao existe.")
    if not login_admin.strip():
        raise ValueError("Informe o login do administrador ativo a promover.")

    # Nenhum arquivo existente sera alterado. Grava em arquivo temporario,
    # validando completamente antes de entregar o novo banco de homologacao.
    fd, nome_temporario = tempfile.mkstemp(
        prefix=".prestserv_migracao_", suffix=".db", dir=saida.parent
    )
    os.close(fd)
    temporario = Path(nome_temporario)

    try:
        with sqlite3.connect(origem.as_uri() + "?mode=ro", uri=True) as fonte:
            with sqlite3.connect(temporario) as destino:
                fonte.backup(destino)

        with sqlite3.connect(temporario) as conexao:
            conexao.execute("PRAGMA foreign_keys = ON")
            versao_inicial = conexao.execute("PRAGMA user_version").fetchone()[0]
            if versao_inicial not in (0, 1):
                raise RuntimeError(
                    f"Esperado banco V1 (esquema 0 ou 1); encontrado {versao_inicial}."
                )

            verificar_integridade(conexao, "Banco de origem copiado")
            antes = contar_registros(conexao)

            # Evita migrar e depois descobrir que o login desejado nao existe.
            usuario = conexao.execute(
                "SELECT id FROM usuarios WHERE login = ? AND perfil = 'admin' AND ativo = 1",
                (login_admin.strip(),),
            ).fetchone()
            if usuario is None:
                raise ValueError("O login indicado nao pertence a um administrador ativo.")

            if versao_inicial == 0:
                criar_estrutura_logs(conexao)   # 0 -> 1

            if not migrar_usuarios_v200(conexao):  # 1 -> 2
                raise RuntimeError("A migracao V1 -> V2 nao foi executada.")

            criar_estrutura_entradas(conexao)
            criar_estrutura_voluntarios(conexao)
            usuario_id = promover_primeiro_superadmin(conexao, login_admin)

            verificar_integridade(conexao, "Banco V2 migrado")
            versao_final = conexao.execute("PRAGMA user_version").fetchone()[0]
            if versao_final != 2:
                raise RuntimeError(f"Versao final inesperada: {versao_final}")
            depois = contar_registros(conexao)
            if antes != depois:
                raise RuntimeError(
                    "Contagem de registros alterada nas tabelas originais: "
                    f"{antes!r} -> {depois!r}"
                )
            papel = conexao.execute(
                "SELECT perfil FROM usuarios WHERE id = ?", (usuario_id,)
            ).fetchone()[0]
            if papel != "superadmin":
                raise RuntimeError("A conta nao foi promovida.")

            for tabela in ("entradas", "voluntarios", "fotos_voluntarios", "presencas_voluntarios"):
                if conexao.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                    (tabela,),
                ).fetchone() is None:
                    raise RuntimeError(f"Tabela nova ausente: {tabela}")

        if saida.exists() or saida.is_symlink():
            raise RuntimeError("O destino passou a existir durante a migracao.")
        os.replace(temporario, saida)
        print("MIGRACAO PARA COPIA: OK")
        print(f"Esquema: {versao_inicial} -> 2")
        print("Integridade e chaves estrangeiras: OK")
        print("Contagens das tabelas originais preservadas: OK")
        print("Tabelas de entradas e voluntarios: OK")
        print("Primeiro superadministrador: OK")
        print(f"Nova copia pronta: {saida}")
        print("O BANCO DE ORIGEM NAO FOI ALTERADO.")
    finally:
        temporario.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origem", required=True, type=Path,
                        help="Banco V1 original, lido sem alteracoes")
    parser.add_argument("--saida", required=True, type=Path,
                        help="Caminho de NOVO arquivo DB para homologacao")
    parser.add_argument("--admin-login", default=None,
                        help="Login de administrador ativo a promover")
    args = parser.parse_args()
    login = args.admin_login
    if login is None:
        login = input("Login do administrador ativo a promover: ").strip()
    migrar_copia(args.origem, args.saida, login)


if __name__ == "__main__":
    main()
