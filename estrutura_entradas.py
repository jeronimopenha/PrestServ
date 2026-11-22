def criar_estrutura_entradas(conexao):
    """
    Cria a estrutura de entradas de doações e compras.

    Compatível com o esquema 2 do PrestServ.
    Não modifica tabelas existentes.
    """

    versao = conexao.execute("PRAGMA user_version").fetchone()[0]

    if versao != 2:
        raise RuntimeError(f"Esquema incompatível para entradas: {versao}")

    with conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS entradas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                data TEXT NOT NULL,

                tipo TEXT NOT NULL CHECK (
                    tipo IN ('doacao', 'compra')
                ),

                categoria TEXT NOT NULL CHECK (
                    length(trim(categoria)) > 0
                ),

                item TEXT NOT NULL CHECK (
                    length(trim(item)) > 0
                ),

                quantidade REAL NOT NULL CHECK (
                    quantidade > 0
                ),

                unidade TEXT NOT NULL CHECK (
                    length(trim(unidade)) > 0
                ),

                origem TEXT,

                valor_centavos INTEGER CHECK (
                    valor_centavos IS NULL OR (
                        typeof(valor_centavos) = 'integer'
                        AND valor_centavos >= 0
                    )
                ),

                usuario_id INTEGER NOT NULL,

                criado_em TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (usuario_id)
                    REFERENCES usuarios(id)
            )
        """)

        colunas = {linha[1] for linha in conexao.execute("PRAGMA table_info(entradas)")}

        esperadas = {
            "id",
            "data",
            "tipo",
            "categoria",
            "item",
            "quantidade",
            "unidade",
            "origem",
            "valor_centavos",
            "usuario_id",
            "criado_em",
        }

        if colunas != esperadas:
            raise RuntimeError("Estrutura da tabela entradas incompatível.")

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_entradas_data
            ON entradas(data)
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_entradas_tipo
            ON entradas(tipo)
        """)
