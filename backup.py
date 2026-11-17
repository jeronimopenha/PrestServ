import sqlite3
from contextlib import closing
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile
from database import conectar, DB_PATH, registrar_log
from permissoes import exigir_permissao_usuario

# Limite de proteção contra arquivos excessivamente grandes.
# Ajustar caso o banco ultrapasse 512 MB.
TAMANHO_MAXIMO = 512 * 1024 * 1024


TABELAS_OBRIGATORIAS = {
    "pessoas",
    "fotos_pessoas",
    "servicos",
    "presencas",
    "presenca_servicos",
    "usuarios",
}

COLUNAS_OBRIGATORIAS = {
    "pessoas": {
        "id",
        "nome",
        "documento",
        "telefone",
        "contato_nome",
        "contato_telefone",
        "ativo",
    },
    "fotos_pessoas": {"pessoa_id", "foto", "formato"},
    "servicos": {"id", "nome", "ativo"},
    "presencas": {"id", "pessoa_id", "data"},
    "presenca_servicos": {"presenca_id", "servico_id"},
    "usuarios": {"id", "nome", "login", "senha_hash", "perfil", "ativo"},
}


def gerar_backup(ator_id):
    """
    Gera um ZIP contendo uma cópia consistente do banco.

    Somente superadministradores ativos podem gerar
    backups completos do PrestServ.
    """

    with closing(conectar()) as origem:
        # Verifica a permissão diretamente no SQLite.
        exigir_permissao_usuario(
            origem,
            ator_id,
            "gerar_backup",
        )

        # Gera uma cópia consistente em memória.
        with closing(sqlite3.connect(":memory:")) as copia:
            origem.backup(copia)
            dados_banco = copia.serialize()

    buffer = BytesIO()

    with ZipFile(
        buffer,
        mode="w",
        compression=ZIP_DEFLATED,
        compresslevel=6,
    ) as zip_file:
        zip_file.writestr(
            "prestserv.db",
            dados_banco,
        )

    return buffer.getvalue()


def validar_banco(conexao):
    """Valida a integridade e a estrutura de um backup."""

    integridade = conexao.execute("PRAGMA integrity_check").fetchone()[0]

    if integridade != "ok":
        raise ValueError("O arquivo SQLite está corrompido.")

    versao = conexao.execute("PRAGMA user_version").fetchone()[0]

    if versao not in (0, 1, 2):
        raise ValueError(f"Versão de backup não suportada: {versao}.")

    tabelas = {
        linha[0]
        for linha in conexao.execute(
            "SELECT name FROM sqlite_master " "WHERE type = 'table'"
        )
    }

    if not TABELAS_OBRIGATORIAS.issubset(tabelas):
        raise ValueError("O arquivo não contém todas as tabelas do PrestServ.")

    for tabela, colunas_esperadas in COLUNAS_OBRIGATORIAS.items():
        colunas = {
            linha[1] for linha in conexao.execute(f"PRAGMA table_info({tabela})")
        }

        if not colunas_esperadas.issubset(colunas):
            raise ValueError(f"Estrutura incompatível na tabela {tabela}.")

    violacoes = conexao.execute("PRAGMA foreign_key_check").fetchall()

    if violacoes:
        raise ValueError("O backup contém referências inválidas " "entre tabelas.")

    if versao in (0, 1):
        # Backups anteriores à V2.
        total = conexao.execute("""
            SELECT COUNT(*)
            FROM usuarios
            WHERE perfil = 'admin'
              AND ativo = 1
        """).fetchone()[0]

        if total == 0:
            raise ValueError("O backup antigo não contém " "um administrador ativo.")

    else:
        # Backups da V2.
        if "logs" not in tabelas:
            raise ValueError("Backup V2 sem tabela de auditoria.")

        total = conexao.execute("""
            SELECT COUNT(*)
            FROM usuarios
            WHERE perfil = 'superadmin'
              AND ativo = 1
        """).fetchone()[0]

        if total == 0:
            raise ValueError("O backup V2 não contém " "um superadministrador ativo.")

    return versao


def restaurar_backup(conteudo_zip, ator_id, ator_login=None):
    """
    Restaura um backup V2 do PrestServ.

    Exige superadministrador ativo e preserva seu
    acesso ao sistema após a restauração.

    Executar somente durante manutenção, sem
    outros usuários utilizando o sistema.
    """

    if not isinstance(conteudo_zip, (bytes, bytearray)):
        raise ValueError("Conteúdo do backup inválido.")

    if len(conteudo_zip) > TAMANHO_MAXIMO:
        raise ValueError("O arquivo ZIP é grande demais.")

    # 1. Verifica a autorização no banco atual.
    with closing(conectar()) as atual:
        exigir_permissao_usuario(
            atual,
            ator_id,
            "restaurar_backup",
        )

        versao_atual = atual.execute("PRAGMA user_version").fetchone()[0]

        if versao_atual != 2:
            raise RuntimeError(
                "A restauração V2 exige um banco " "atualizado para o esquema 2."
            )

        ator = atual.execute(
            """
            SELECT login, senha_hash
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

        login_atual = ator[0]
        hash_atual = ator[1]

    # 2. Extrai e valida o ZIP.
    try:
        with ZipFile(BytesIO(conteudo_zip), "r") as arquivo:
            entradas = arquivo.infolist()

            if (
                len(entradas) != 1
                or entradas[0].filename != "prestserv.db"
                or entradas[0].is_dir()
            ):
                raise ValueError("O ZIP deve conter somente prestserv.db.")

            if entradas[0].file_size > TAMANHO_MAXIMO:
                raise ValueError("O banco descompactado é grande demais.")

            with arquivo.open(entradas[0]) as entrada:
                dados_banco = entrada.read(TAMANHO_MAXIMO + 1)

            if len(dados_banco) > TAMANHO_MAXIMO:
                raise ValueError("O banco ultrapassa o tamanho permitido.")

    except BadZipFile as erro:
        raise ValueError("O arquivo enviado não é um ZIP válido.") from erro

    if not dados_banco.startswith(b"SQLite format 3\x00"):
        raise ValueError("O ZIP não contém um banco SQLite válido.")

    # 3. Carrega e valida o banco em memória.
    with closing(sqlite3.connect(":memory:")) as origem:
        try:
            origem.deserialize(dados_banco)
            versao_backup = validar_banco(origem)

        except sqlite3.DatabaseError as erro:
            raise ValueError("O banco do backup está inválido.") from erro

        if versao_backup != 2:
            raise ValueError(
                "Este backup pertence a uma versão antiga. "
                "A migração deve ser realizada antes "
                "da restauração."
            )

        # 4. Confirma que o responsável continuará
        # conseguindo entrar depois da restauração.
        usuario_backup = origem.execute(
            """
            SELECT login, senha_hash, perfil, ativo
            FROM usuarios
            WHERE id = ?
            """,
            (ator_id,),
        ).fetchone()

        if (
            usuario_backup is None
            or usuario_backup[0] != login_atual
            or usuario_backup[1] != hash_atual
            or usuario_backup[2] != "superadmin"
            or usuario_backup[3] != 1
        ):
            raise ValueError(
                "A restauração foi bloqueada porque "
                "o superadministrador responsável "
                "perderia seu acesso atual. "
                "Utilize um procedimento de recuperação "
                "administrativa."
            )

        # 5. Registra a restauração no banco
        # que será efetivamente restaurado.
        registrar_log(
            origem,
            acao="restaurar_backup",
            usuario_id=ator_id,
            usuario_login=login_atual,
            entidade="sistema",
            detalhes={
                "versao_backup": versao_backup,
                "tamanho_zip_bytes": len(conteudo_zip),
            },
        )

        origem.commit()

        # 6. Revalida o operador e substitui o banco.
        # Deve ser executado sem outras sessões ativas.
        with closing(conectar()) as destino:
            exigir_permissao_usuario(
                destino,
                ator_id,
                "restaurar_backup",
            )

            origem.backup(destino)
