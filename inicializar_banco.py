import sqlite3

from database import DB_PATH


def inicializar_banco():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conexao:
        conexao.execute("PRAGMA foreign_keys = ON")

        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS pessoas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                documento TEXT,
                telefone TEXT,
                contato_nome TEXT,
                contato_telefone TEXT,
                ativo INTEGER NOT NULL DEFAULT 1
                    CHECK (ativo IN (0, 1)),
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS fotos_pessoas (
                pessoa_id INTEGER PRIMARY KEY,
                foto BLOB NOT NULL,
                formato TEXT NOT NULL DEFAULT 'image/jpeg',
                atualizada_em TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pessoa_id)
                    REFERENCES pessoas(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                ativo INTEGER NOT NULL DEFAULT 1
                    CHECK (ativo IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS presencas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pessoa_id INTEGER NOT NULL,
                data TEXT NOT NULL
                    DEFAULT (date('now', 'localtime')),
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pessoa_id) REFERENCES pessoas(id),
                UNIQUE (pessoa_id, data)
            );

            CREATE TABLE IF NOT EXISTS presenca_servicos (
                presenca_id INTEGER NOT NULL,
                servico_id INTEGER NOT NULL,
                PRIMARY KEY (presenca_id, servico_id),
                FOREIGN KEY (presenca_id)
                    REFERENCES presencas(id) ON DELETE CASCADE,
                FOREIGN KEY (servico_id)
                    REFERENCES servicos(id)
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL
                    CHECK (perfil IN ('admin', 'porteiro')),
                ativo INTEGER NOT NULL DEFAULT 1
                    CHECK (ativo IN (0, 1)),
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_pessoas_nome
                ON pessoas(nome);

            CREATE INDEX IF NOT EXISTS idx_presencas_data
                ON presencas(data);

            CREATE INDEX IF NOT EXISTS idx_presencas_pessoa
                ON presencas(pessoa_id);

            INSERT OR IGNORE INTO servicos(nome)
            VALUES ('Jantar'), ('Banho'), ('Roupas');
        """)


if __name__ == "__main__":
    inicializar_banco()
    print(f"Banco inicializado: {DB_PATH}")
