"""PrestServ V1.1.0 — etapa 2: esquema de logs e inspeção de vínculos.

Este módulo NÃO apaga nem desativa cadastros, NÃO escreve logs operacionais
(e eles serão adicionados na etapa 3), nem altera tabelas já existentes.
"""

import sqlite3
from pathlib import Path

CAMINHO_BANCO = Path(__file__).resolve().parent / "dados" / "prestserv.db"

# Relações inferidas por convenção, mesmo sem FOREIGN KEY declarada.
# Os logs são excluídos intencionalmente: guardam uma cópia do operador,
# e não devem impedir a exclusão de uma conta sem vínculos operacionais.
COLUNAS_PROVAVEIS = {
    "pessoas": {"pessoa_id", "id_pessoa"},
    "usuarios": {"usuario_id", "id_usuario"},
}


def _identificador(nome: str) -> str:
    """Protege identificadores de SQL obtidos do esquema SQLite."""
    return '"' + nome.replace('"', '""') + '"'


def _tabelas(conexao: sqlite3.Connection) -> list[str]:
    return [
        linha[0]
        for linha in conexao.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    ]


def _colunas(conexao: sqlite3.Connection, tabela: str) -> list[str]:
    return [
        linha[1] for linha in conexao.execute(
            f"PRAGMA table_info({_identificador(tabela)})"
        )
    ]


def criar_estrutura_logs(conexao: sqlite3.Connection) -> None:
    """Cria somente o que não existe; mantém dados já cadastrados."""
    with conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criado_em TEXT NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                usuario_id INTEGER,
                usuario_login TEXT,
                acao TEXT NOT NULL,
                entidade TEXT,
                entidade_id INTEGER,
                resultado TEXT NOT NULL DEFAULT 'sucesso',
                detalhes_json TEXT
            )
        """)
        esperadas = {
            "id", "criado_em", "usuario_id", "usuario_login", "acao",
            "entidade", "entidade_id", "resultado", "detalhes_json",
        }
        atuais = set(_colunas(conexao, "logs"))
        if not esperadas.issubset(atuais):
            raise RuntimeError(
                "A tabela logs existente tem outra estrutura. "
                "Não vou alterá-la automaticamente."
            )
        conexao.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_criado_em "
            "ON logs(criado_em)"
        )
        conexao.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_usuario_id "
            "ON logs(usuario_id)"
        )
        conexao.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_acao "
            "ON logs(acao)"
        )
        conexao.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_entidade "
            "ON logs(entidade, entidade_id)"
        )


def consultar_vinculos(
    conexao: sqlite3.Connection,
    tabela_alvo: str,
    registro_id: int,
) -> list[dict]:
    """Retorna vínculos diretos; não exclui, desativa ou altera registros.

    Procura FKs declaradas e colunas de referência convencionais.
    Para os casos de FKs compostas/não usuais, o bloqueio definitivo
    ainda precisa ser coberto pela regra de negócio da etapa 4.
    """
    if tabela_alvo not in ("pessoas", "usuarios"):
        raise ValueError("Somente pessoas e usuarios são permitidos.")
    if type(registro_id) is not int or registro_id <= 0:
        raise ValueError("ID do registro deve ser inteiro positivo.")

    tabelas = _tabelas(conexao)
    if tabela_alvo not in tabelas:
        raise ValueError(f"Tabela não encontrada: {tabela_alvo}")

    # O esquema já conhecido usa PK id. Falha em vez de presumir que
    # a checagem é suficiente caso esse campo seja alterado.
    if "id" not in _colunas(conexao, tabela_alvo):
        raise RuntimeError(f"{tabela_alvo} não possui coluna id.")

    encontrados = []
    for tabela in tabelas:
        if tabela in (tabela_alvo, "logs"):
            continue

        colunas_existentes = set(_colunas(conexao, tabela))
        referencias = COLUNAS_PROVAVEIS[tabela_alvo] & colunas_existentes

        for fk in conexao.execute(
            f"PRAGMA foreign_key_list({_identificador(tabela)})"
        ):
            # PRAGMA: id, seq, table, from, to, on_update, on_delete, match
            if fk[2] == tabela_alvo:
                # Se a FK aponta para outro campo (ou é composta), a
                # exclusão só pode ser avaliada após análise específica.
                if fk[4] not in (None, "id"):
                    raise RuntimeError(
                        f"FK não usual em {tabela}.{fk[3]} -> "
                        f"{tabela_alvo}.{fk[4]}; verificar manualmente."
                    )
                referencias.add(fk[3])

        for coluna in sorted(referencias):
            total = conexao.execute(
                f"SELECT COUNT(*) FROM {_identificador(tabela)} "
                f"WHERE {_identificador(coluna)} = ?",
                (registro_id,),
            ).fetchone()[0]
            if total:
                encontrados.append(
                    {"tabela": tabela, "coluna": coluna, "quantidade": total}
                )
    return encontrados


def preparar_banco() -> None:
    """Executa migração isolada em banco já inicializado."""
    if not CAMINHO_BANCO.is_file():
        raise FileNotFoundError(
            f"Banco não encontrado em {CAMINHO_BANCO}. "
            "Inicialize o PrestServ antes de executar este script."
        )
    with sqlite3.connect(CAMINHO_BANCO, timeout=10) as conexao:
        conexao.execute("PRAGMA foreign_keys=ON")
        criar_estrutura_logs(conexao)
        total = conexao.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
        print(f"Estrutura V1.1.0 preparada. Logs existentes: {total}.")
        print("Tabelas:", ", ".join(_tabelas(conexao)))


if __name__ == "__main__":
    preparar_banco()
