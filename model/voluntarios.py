"""Operações de cadastro dos voluntários."""

from datetime import date
from conn.database import conectar, registrar_log, data_atual
from model.permissoes import exigir_permissao_usuario, tem_permissao
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError


def _validar_dados(nome, telefone):
    """Normaliza e valida os dados do voluntário."""

    if not isinstance(nome, str):
        raise ValueError("Nome inválido.")

    nome = nome.strip()

    if not nome:
        raise ValueError("O nome é obrigatório.")

    if len(nome) > 150:
        raise ValueError("O nome deve ter até 150 caracteres.")

    if telefone is not None:
        if not isinstance(telefone, str):
            raise ValueError("Telefone inválido.")

        telefone = telefone.strip() or None

        if telefone and len(telefone) > 30:
            raise ValueError("O telefone deve ter até 30 caracteres.")

    return nome, telefone


def _validar_id(voluntario_id):
    if type(voluntario_id) is not int or voluntario_id <= 0:
        raise ValueError("Identificador de voluntário inválido.")


def cadastrar_voluntario(nome, telefone=None, *, ator_id):
    """Cadastra um voluntário ativo e registra a auditoria."""

    nome, telefone = _validar_dados(nome, telefone)

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(conexao, ator_id, "cadastrar_voluntarios")

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        cursor = conexao.execute(
            """
            INSERT INTO voluntarios (nome, telefone)
            VALUES (?, ?)
            """,
            (nome, telefone),
        )

        voluntario_id = cursor.lastrowid

        registrar_log(
            conexao,
            acao="cadastrar_voluntario",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="voluntarios",
            entidade_id=voluntario_id,
        )

        return voluntario_id


def listar_voluntarios(*, ator_id, somente_ativos=False):
    """Lista voluntários sem expor contatos ao porteiro."""

    if type(somente_ativos) is not bool:
        raise ValueError("Filtro de situação inválido.")

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(conexao, ator_id, "consultar_voluntarios")

        pode_ver_contato = tem_permissao(perfil, "consultar_contato_voluntarios")

        if pode_ver_contato:
            campos = "id, nome, telefone, ativo, criado_em"
        else:
            campos = "id, nome, ativo"

        # O porteiro consulta somente voluntários ativos.
        filtrar_ativos = somente_ativos or perfil == "porteiro"

        where = "WHERE ativo = 1" if filtrar_ativos else ""

        registros = conexao.execute(f"""
            SELECT {campos}
            FROM voluntarios
            {where}
            ORDER BY nome COLLATE NOCASE, id
            """).fetchall()

        return [dict(registro) for registro in registros]


def buscar_voluntario(voluntario_id, *, ator_id):
    """Consulta um voluntário respeitando dados restritos."""

    _validar_id(voluntario_id)

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(conexao, ator_id, "consultar_voluntarios")

        pode_ver_contato = tem_permissao(perfil, "consultar_contato_voluntarios")

        if pode_ver_contato:
            campos = "id, nome, telefone, ativo, criado_em"
        else:
            campos = "id, nome, ativo"

        registro = conexao.execute(
            f"""
            SELECT {campos}
            FROM voluntarios
            WHERE id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        if registro is None:
            return None

        if perfil == "porteiro" and not registro["ativo"]:
            return None

        return dict(registro)


def atualizar_voluntario(voluntario_id, nome, telefone=None, *, ator_id):
    """Atualiza os dados cadastrais e audita as mudanças."""

    _validar_id(voluntario_id)
    nome, telefone = _validar_dados(nome, telefone)

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(conexao, ator_id, "editar_voluntarios")

        anterior = conexao.execute(
            """
            SELECT nome, telefone
            FROM voluntarios
            WHERE id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        if anterior is None:
            raise ValueError("Voluntário não encontrado.")

        nome_alterado = anterior["nome"] != nome
        telefone_alterado = anterior["telefone"] != telefone

        if not nome_alterado and not telefone_alterado:
            return False

        conexao.execute(
            """
            UPDATE voluntarios
            SET nome = ?, telefone = ?
            WHERE id = ?
            """,
            (nome, telefone, voluntario_id),
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao="atualizar_voluntario",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="voluntarios",
            entidade_id=voluntario_id,
            detalhes={
                "nome_alterado": nome_alterado,
                "telefone_alterado": telefone_alterado,
            },
        )

        return True


def alterar_situacao_voluntario(voluntario_id, ativo, *, ator_id):
    """Ativa ou desativa um voluntário sem apagar seu histórico."""

    _validar_id(voluntario_id)

    if type(ativo) is not bool:
        raise ValueError("A situação deve ser True ou False.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(conexao, ator_id, "editar_voluntarios")

        anterior = conexao.execute(
            """
            SELECT ativo
            FROM voluntarios
            WHERE id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        if anterior is None:
            raise ValueError("Voluntário não encontrado.")

        ativo_anterior = bool(anterior["ativo"])

        if ativo_anterior == ativo:
            return False

        conexao.execute(
            """
            UPDATE voluntarios
            SET ativo = ?
            WHERE id = ?
            """,
            (int(ativo), voluntario_id),
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao=("ativar_voluntario" if ativo else "desativar_voluntario"),
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="voluntarios",
            entidade_id=voluntario_id,
            detalhes={
                "ativo_anterior": ativo_anterior,
                "ativo_novo": ativo,
            },
        )

        return True


def excluir_voluntario(voluntario_id, *, ator_id):
    """
    Exclui um cadastro somente quando não possui presenças.
    A fotografia vinculada é excluída por ON DELETE CASCADE.
    """

    _validar_id(voluntario_id)

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(conexao, ator_id, "excluir_voluntarios")

        existe = conexao.execute(
            """
            SELECT id
            FROM voluntarios
            WHERE id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        if existe is None:
            raise ValueError("Voluntário não encontrado.")

        total_presencas = conexao.execute(
            """
            SELECT COUNT(*)
            FROM presencas_voluntarios
            WHERE voluntario_id = ?
            """,
            (voluntario_id,),
        ).fetchone()[0]

        if total_presencas:
            raise ValueError(
                "Este voluntário possui presenças registradas. "
                "Desative o cadastro para preservar o histórico."
            )

        conexao.execute(
            "DELETE FROM voluntarios WHERE id = ?",
            (voluntario_id,),
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao="excluir_voluntario",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="voluntarios",
            entidade_id=voluntario_id,
        )

        return True


def _preparar_foto_voluntario(conteudo):
    """Valida, redimensiona e converte uma imagem para JPEG."""

    if not isinstance(conteudo, (bytes, bytearray)):
        raise ValueError("Arquivo de imagem inválido.")

    if not conteudo or len(conteudo) > 8 * 1024 * 1024:
        raise ValueError("A imagem deve ter até 8 MB.")

    try:
        with Image.open(BytesIO(conteudo)) as original:
            if original.width * original.height > 20_000_000:
                raise ValueError("Resolução da imagem muito alta.")

            imagem = ImageOps.exif_transpose(original)
            imagem = imagem.convert("RGBA")

            # Converte transparência em fundo branco.
            fundo = Image.new("RGB", imagem.size, "white")
            fundo.paste(imagem, mask=imagem.getchannel("A"))

            fundo.thumbnail((800, 800), Image.Resampling.LANCZOS)

            saida = BytesIO()
            fundo.save(
                saida,
                format="JPEG",
                quality=85,
                optimize=True,
            )

            return saida.getvalue()

    except (UnidentifiedImageError, OSError) as erro:
        raise ValueError("O arquivo não contém uma imagem válida.") from erro


def salvar_foto_voluntario(voluntario_id, conteudo, *, ator_id):
    """Adiciona ou substitui a fotografia de um voluntário."""

    _validar_id(voluntario_id)
    foto_jpeg = _preparar_foto_voluntario(conteudo)

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(conexao, ator_id, "editar_voluntarios")

        existe = conexao.execute(
            "SELECT id FROM voluntarios WHERE id = ?",
            (voluntario_id,),
        ).fetchone()

        if existe is None:
            raise ValueError("Voluntário não encontrado.")

        anterior = conexao.execute(
            """
            SELECT foto
            FROM fotos_voluntarios
            WHERE voluntario_id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        if anterior is not None and anterior["foto"] == foto_jpeg:
            return False

        conexao.execute(
            """
            INSERT INTO fotos_voluntarios (
                voluntario_id, foto, formato
            )
            VALUES (?, ?, 'image/jpeg')
            ON CONFLICT(voluntario_id)
            DO UPDATE SET
                foto = excluded.foto,
                formato = excluded.formato,
                atualizada_em = CURRENT_TIMESTAMP
            """,
            (voluntario_id, foto_jpeg),
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao=(
                "atualizar_foto_voluntario"
                if anterior is not None
                else "adicionar_foto_voluntario"
            ),
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="voluntarios",
            entidade_id=voluntario_id,
        )

        return True


def buscar_foto_voluntario(voluntario_id, *, ator_id):
    """Retorna o JPEG somente a usuários autorizados."""

    _validar_id(voluntario_id)

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(
            conexao, ator_id, "consultar_fotos_voluntarios"
        )

        voluntario = conexao.execute(
            "SELECT ativo FROM voluntarios WHERE id = ?",
            (voluntario_id,),
        ).fetchone()

        if voluntario is None:
            return None

        if perfil == "porteiro" and not voluntario["ativo"]:
            return None

        registro = conexao.execute(
            """
            SELECT foto
            FROM fotos_voluntarios
            WHERE voluntario_id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        return bytes(registro["foto"]) if registro else None


def remover_foto_voluntario(voluntario_id, *, ator_id):
    """Remove uma fotografia, preservando o cadastro."""

    _validar_id(voluntario_id)

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(conexao, ator_id, "editar_voluntarios")

        existe = conexao.execute(
            "SELECT id FROM voluntarios WHERE id = ?",
            (voluntario_id,),
        ).fetchone()

        if existe is None:
            raise ValueError("Voluntário não encontrado.")

        cursor = conexao.execute(
            """
            DELETE FROM fotos_voluntarios
            WHERE voluntario_id = ?
            """,
            (voluntario_id,),
        )

        if cursor.rowcount == 0:
            return False

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao="remover_foto_voluntario",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="voluntarios",
            entidade_id=voluntario_id,
        )

        return True


def registrar_presenca_voluntario(voluntario_id, data=None, *, ator_id):
    """
    Registra a presença de um voluntário.

    Retorna:
        True: presença registrada.
        False: presença já existente.
    """

    _validar_id(voluntario_id)

    hoje = data_atual()
    data = hoje if data is None else data

    try:
        if not isinstance(data, str):
            raise ValueError()

        data_validada = date.fromisoformat(data)

        if data != data_validada.isoformat():
            raise ValueError()

    except ValueError:
        raise ValueError("Data de presença inválida.") from None

    if data_validada > date.fromisoformat(hoje):
        raise ValueError("Não é permitido registrar presenças futuras.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        exigir_permissao_usuario(
            conexao,
            ator_id,
            "registrar_presenca_voluntarios",
        )

        # Datas anteriores são restritas aos administradores.
        if data != hoje:
            exigir_permissao_usuario(
                conexao,
                ator_id,
                "alterar_data_presenca_voluntarios",
            )

        voluntario = conexao.execute(
            """
            SELECT ativo
            FROM voluntarios
            WHERE id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        if voluntario is None:
            raise ValueError("Voluntário não encontrado.")

        if not voluntario["ativo"]:
            raise ValueError(
                "Não é permitido registrar presença " "de um voluntário inativo."
            )

        anterior = conexao.execute(
            """
            SELECT id
            FROM presencas_voluntarios
            WHERE voluntario_id = ?
              AND data = ?
            """,
            (voluntario_id, data),
        ).fetchone()

        if anterior is not None:
            return False

        cursor = conexao.execute(
            """
            INSERT INTO presencas_voluntarios (
                voluntario_id,
                data,
                usuario_id
            )
            VALUES (?, ?, ?)
            """,
            (voluntario_id, data, ator_id),
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao="registrar_presenca_voluntario",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="presencas_voluntarios",
            entidade_id=cursor.lastrowid,
            detalhes={
                "voluntario_id": voluntario_id,
                "data": data,
            },
        )

        return True


def _validar_data_presenca_voluntario(data):
    """Normaliza uma data e impede datas futuras."""

    hoje = data_atual()
    data = hoje if data is None else data

    try:
        if not isinstance(data, str):
            raise ValueError()

        data_validada = date.fromisoformat(data)

        if data != data_validada.isoformat():
            raise ValueError()

    except ValueError:
        raise ValueError("Data de presença inválida.") from None

    if data_validada > date.fromisoformat(hoje):
        raise ValueError("Não é permitido consultar ou alterar presenças futuras.")

    return data, hoje


def listar_presencas_voluntarios(data=None, *, ator_id):
    """Lista as presenças de voluntários em uma data."""

    with conectar() as conexao:
        perfil = exigir_permissao_usuario(
            conexao,
            ator_id,
            "registrar_presenca_voluntarios",
        )

        data, hoje = _validar_data_presenca_voluntario(data)

        if data != hoje:
            exigir_permissao_usuario(
                conexao,
                ator_id,
                "alterar_data_presenca_voluntarios",
            )

        # Porteiros só visualizam voluntários ativos.
        filtro_ativos = "AND v.ativo = 1" if perfil == "porteiro" else ""

        registros = conexao.execute(
            f"""
            SELECT
                p.id,
                p.voluntario_id,
                v.nome,
                v.ativo,
                p.data,
                p.criado_em
            FROM presencas_voluntarios AS p
            JOIN voluntarios AS v
              ON v.id = p.voluntario_id
            WHERE p.data = ?
            {filtro_ativos}
            ORDER BY v.nome COLLATE NOCASE, p.id
            """,
            (data,),
        ).fetchall()

        return [dict(registro) for registro in registros]


def remover_presenca_voluntario(voluntario_id, data=None, *, ator_id):
    """
    Remove uma presença respeitando datas e permissões.

    Retorna:
        True: presença removida.
        False: presença inexistente.
    """

    _validar_id(voluntario_id)

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")

        perfil = exigir_permissao_usuario(
            conexao,
            ator_id,
            "registrar_presenca_voluntarios",
        )

        data, hoje = _validar_data_presenca_voluntario(data)

        if data != hoje:
            exigir_permissao_usuario(
                conexao,
                ator_id,
                "alterar_data_presenca_voluntarios",
            )

        voluntario = conexao.execute(
            """
            SELECT ativo
            FROM voluntarios
            WHERE id = ?
            """,
            (voluntario_id,),
        ).fetchone()

        if voluntario is None:
            raise ValueError("Voluntário não encontrado.")

        if perfil == "porteiro" and not voluntario["ativo"]:
            raise PermissionError(
                "O porteiro não pode alterar presenças " "de voluntários inativos."
            )

        presenca = conexao.execute(
            """
            SELECT id
            FROM presencas_voluntarios
            WHERE voluntario_id = ?
              AND data = ?
            """,
            (voluntario_id, data),
        ).fetchone()

        if presenca is None:
            return False

        conexao.execute(
            """
            DELETE FROM presencas_voluntarios
            WHERE id = ?
            """,
            (presenca["id"],),
        )

        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?",
            (ator_id,),
        ).fetchone()

        registrar_log(
            conexao,
            acao="remover_presenca_voluntario",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="presencas_voluntarios",
            entidade_id=presenca["id"],
            detalhes={
                "voluntario_id": voluntario_id,
                "data": data,
            },
        )

        return True
