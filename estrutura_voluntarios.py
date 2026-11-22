def criar_estrutura_voluntarios(conexao):
    """
    Cria as tabelas de voluntários do PrestServ V2.0.0.

    - Exige o esquema 2.
    - Preserva dados existentes.
    - Pode ser executada repetidamente.
    """

    versao = conexao.execute("PRAGMA user_version").fetchone()[0]

    if versao != 2:
        raise RuntimeError(f"Esquema incompatível para voluntários: {versao}")

    # Permite desfazer toda a criação se houver erro.
    conexao.execute("SAVEPOINT estrutura_voluntarios")

    try:
        # Cadastro de voluntários.
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS voluntarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nome TEXT NOT NULL
                    CHECK (length(trim(nome)) > 0),

                telefone TEXT,

                ativo INTEGER NOT NULL DEFAULT 1
                    CHECK (ativo IN (0, 1)),

                criado_em TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Fotografias opcionais.
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS fotos_voluntarios (
                voluntario_id INTEGER PRIMARY KEY,

                foto BLOB NOT NULL,

                formato TEXT NOT NULL
                    DEFAULT 'image/jpeg',

                atualizada_em TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (voluntario_id)
                    REFERENCES voluntarios(id)
                    ON DELETE CASCADE
            )
        """)

        # Uma presença por voluntário em cada dia.
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS presencas_voluntarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                voluntario_id INTEGER NOT NULL,

                data TEXT NOT NULL,

                usuario_id INTEGER NOT NULL,

                criado_em TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (voluntario_id)
                    REFERENCES voluntarios(id)
                    ON DELETE RESTRICT,

                FOREIGN KEY (usuario_id)
                    REFERENCES usuarios(id)
                    ON DELETE RESTRICT,

                UNIQUE (voluntario_id, data)
            )
        """)

        # Verifica se as tabelas têm as colunas esperadas.
        esperadas = {
            "voluntarios": {
                "id",
                "nome",
                "telefone",
                "ativo",
                "criado_em",
            },
            "fotos_voluntarios": {
                "voluntario_id",
                "foto",
                "formato",
                "atualizada_em",
            },
            "presencas_voluntarios": {
                "id",
                "voluntario_id",
                "data",
                "usuario_id",
                "criado_em",
            },
        }

        for tabela, colunas_esperadas in esperadas.items():
            colunas = {
                linha[1] for linha in conexao.execute(f"PRAGMA table_info({tabela})")
            }

            if colunas != colunas_esperadas:
                raise RuntimeError(f"Estrutura incompatível na tabela {tabela}.")

        # Índices para pesquisas e relatórios.
        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_voluntarios_nome
            ON voluntarios(nome)
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_presencas_voluntarios_data
            ON presencas_voluntarios(data)
        """)

        conexao.execute("RELEASE SAVEPOINT estrutura_voluntarios")

    except Exception:
        conexao.execute("ROLLBACK TO SAVEPOINT estrutura_voluntarios")
        conexao.execute("RELEASE SAVEPOINT estrutura_voluntarios")
        raise
