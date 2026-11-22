import sqlite3

PAPEIS = (
    "superadmin",
    "admin",
    "secretaria",
    "porteiro",
    "consulta",
)


def migrar_usuarios_v200(conexao):
    """
    Atualiza a tabela usuarios para os cinco papéis.

    Preserva IDs, nomes, logins, hashes de senhas,
    situações das contas e datas de criação.

    Não promove ninguém automaticamente.
    """

    versao = conexao.execute("PRAGMA user_version").fetchone()[0]

    if versao == 2:
        colunas = {
            linha[1]: linha
            for linha in conexao.execute("PRAGMA table_info(presenca_servicos)")
        }

        quantidade = colunas.get("quantidade")

        if (
            quantidade is None
            or quantidade[2].upper() != "INTEGER"
            or quantidade[3] != 1
            or str(quantidade[4]).strip("()'\" ") != "1"
        ):
            raise RuntimeError(
                "Banco marcado como V2, mas sem a " "estrutura esperada de quantidades."
            )

        return False

    if versao != 1:
        raise RuntimeError(f"Versão de banco incompatível: {versao}")

    if conexao.in_transaction:
        raise RuntimeError("A migração precisa iniciar fora de uma transação.")

    # Confere a estrutura existente.
    colunas = {linha[1] for linha in conexao.execute("PRAGMA table_info(usuarios)")}

    esperadas = {
        "id",
        "nome",
        "login",
        "senha_hash",
        "perfil",
        "ativo",
        "criado_em",
    }

    if colunas != esperadas:
        raise RuntimeError("Estrutura inesperada na tabela usuarios.")

    # Evita perder índices ou gatilhos personalizados.
    objetos = conexao.execute("""
        SELECT name
        FROM sqlite_master
        WHERE tbl_name = 'usuarios'
          AND type IN ('index', 'trigger')
          AND sql IS NOT NULL
    """).fetchall()

    if objetos:
        raise RuntimeError(
            "Existem índices ou gatilhos personalizados "
            "na tabela usuarios. Revisar antes da migração."
        )

    # Verifica relacionamentos externos.
    tabelas = conexao.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
    """).fetchall()

    for (tabela,) in tabelas:
        if tabela == "usuarios":
            continue

        nome_seguro = tabela.replace('"', '""')

        for fk in conexao.execute(f'PRAGMA foreign_key_list("{nome_seguro}")'):
            if fk[2] == "usuarios":
                raise RuntimeError(
                    f"A tabela {tabela} referencia usuarios. "
                    "A migração precisa ser revisada."
                )

    sequencia = conexao.execute("""
        SELECT seq
        FROM sqlite_sequence
        WHERE name = 'usuarios'
    """).fetchone()

    ultimo_id = sequencia[0] if sequencia else 0

    try:
        conexao.execute("BEGIN IMMEDIATE")

        conexao.execute("""
            CREATE TABLE usuarios_v200 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL CHECK (
                    perfil IN (
                        'superadmin',
                        'admin',
                        'secretaria',
                        'porteiro',
                        'consulta'
                    )
                ),
                ativo INTEGER NOT NULL DEFAULT 1
                    CHECK (ativo IN (0, 1)),
                criado_em TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conexao.execute("""
            INSERT INTO usuarios_v200 (
                id, nome, login, senha_hash,
                perfil, ativo, criado_em
            )
            SELECT
                id, nome, login, senha_hash,
                perfil, ativo, criado_em
            FROM usuarios
        """)

        conexao.execute("DROP TABLE usuarios")

        conexao.execute("""
            ALTER TABLE usuarios_v200
            RENAME TO usuarios
        """)

        # Preserva o histórico do AUTOINCREMENT.
        conexao.execute(
            """
            UPDATE sqlite_sequence
            SET seq = MAX(seq, ?)
            WHERE name = 'usuarios'
        """,
            (ultimo_id,),
        )

        # V2.0.0: adiciona quantidades aos serviços.
        # Os registros existentes recebem quantidade 1.
        conexao.execute("""
            ALTER TABLE presenca_servicos
            ADD COLUMN quantidade INTEGER NOT NULL DEFAULT 1
                CHECK (
                    typeof(quantidade) = 'integer'
                    AND quantidade >= 1
                )
        """)

        # V2.0.0: informações complementares dos cadastros.
        conexao.execute("""
            ALTER TABLE pessoas
            ADD COLUMN endereco TEXT
        """)

        conexao.execute("""
            ALTER TABLE pessoas
            ADD COLUMN observacoes TEXT
        """)

        # NULL: não informado
        # 0: não autorizado
        # 1: autorizado
        conexao.execute("""
            ALTER TABLE pessoas
            ADD COLUMN autorizado_refeicao_local INTEGER
                DEFAULT NULL
                CHECK (
                    autorizado_refeicao_local IN (0, 1)
                )
        """)

        conexao.execute("PRAGMA user_version = 2")

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    return True


def promover_primeiro_superadmin(conexao, login):
    """
    Promove um administrador ativo a superadministrador.

    Operação destinada à migração inicial para a V2.0.
    Não deve ser disponibilizada como ação da interface.
    """
    from database import registrar_log

    if not isinstance(login, str) or not login.strip():
        raise ValueError("Informe o login do administrador.")

    login = login.strip()

    if conexao.in_transaction:
        raise RuntimeError("A promoção precisa iniciar fora de uma transação.")

    try:
        conexao.execute("BEGIN IMMEDIATE")

        versao = conexao.execute("PRAGMA user_version").fetchone()[0]

        if versao != 2:
            raise RuntimeError("Execute primeiro a migração para a versão 2.")

        total = conexao.execute("""
            SELECT COUNT(*)
            FROM usuarios
            WHERE perfil = 'superadmin'
        """).fetchone()[0]

        if total:
            raise ValueError("Já existe um superadministrador cadastrado.")

        usuario = conexao.execute(
            """
            SELECT id, perfil, ativo
            FROM usuarios
            WHERE login = ?
        """,
            (login,),
        ).fetchone()

        if usuario is None:
            raise ValueError("Usuário não encontrado.")

        usuario_id, perfil, ativo = usuario

        if perfil != "admin" or not ativo:
            raise ValueError("O usuário precisa ser administrador ativo.")

        conexao.execute(
            """
            UPDATE usuarios
            SET perfil = 'superadmin'
            WHERE id = ?
        """,
            (usuario_id,),
        )

        registrar_log(
            conexao,
            acao="promover_primeiro_superadmin",
            entidade="usuarios",
            entidade_id=usuario_id,
            detalhes={"origem": "migracao_v200"},
        )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    return usuario_id
