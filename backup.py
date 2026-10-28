import sqlite3
from contextlib import closing
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile
from database import conectar, DB_PATH

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


def gerar_backup():
    """Gera um ZIP em memória com uma cópia consistente do SQLite."""

    with closing(conectar()) as origem:
        with closing(sqlite3.connect(":memory:")) as copia:
            origem.backup(copia)
            dados_banco = copia.serialize()

    buffer = BytesIO()

    with ZipFile(
        buffer, mode="w", compression=ZIP_DEFLATED, compresslevel=6
    ) as zip_file:
        zip_file.writestr("prestserv.db", dados_banco)

    return buffer.getvalue()


def validar_banco(conexao):
    resultado = conexao.execute("PRAGMA integrity_check").fetchone()[0]

    if resultado != "ok":
        raise ValueError("O arquivo SQLite está corrompido.")

    tabelas = {
        linha[0]
        for linha in conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
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
        raise ValueError("O backup contém referências inválidas entre tabelas.")

    admins = conexao.execute("""
        SELECT COUNT(*)
        FROM usuarios
        WHERE perfil = 'admin' AND ativo = 1
        """).fetchone()[0]

    if admins == 0:
        raise ValueError("O backup não contém um administrador ativo.")


def restaurar_backup(conteudo_zip):
    """
    Restaura um banco enviado em ZIP.

    Executar apenas durante manutenção, sem outros
    usuários utilizando o PrestServ.
    """

    if len(conteudo_zip) > TAMANHO_MAXIMO:
        raise ValueError("O arquivo ZIP é grande demais.")

    try:
        with ZipFile(BytesIO(conteudo_zip), "r") as zip_file:
            arquivos = zip_file.infolist()

            if (
                len(arquivos) != 1
                or arquivos[0].filename != "prestserv.db"
                or arquivos[0].is_dir()
            ):
                raise ValueError("O ZIP deve conter somente prestserv.db.")

            if arquivos[0].file_size > TAMANHO_MAXIMO:
                raise ValueError("O banco descompactado é grande demais.")

            with zip_file.open(arquivos[0]) as arquivo:
                dados_banco = arquivo.read(TAMANHO_MAXIMO + 1)

            if len(dados_banco) > TAMANHO_MAXIMO:
                raise ValueError("O banco ultrapassa o tamanho permitido.")

    except BadZipFile as erro:
        raise ValueError("O arquivo enviado não é um ZIP válido.") from erro

    if not dados_banco.startswith(b"SQLite format 3\x00"):
        raise ValueError("O ZIP não contém um banco SQLite válido.")

    with closing(sqlite3.connect(":memory:")) as origem:
        try:
            origem.deserialize(dados_banco)
            validar_banco(origem)
        except sqlite3.DatabaseError as erro:
            raise ValueError("O banco do backup está inválido ou corrompido.") from erro

        # Somente executar sem outros usuários conectados.
        with closing(conectar()) as destino:
            origem.backup(destino)
