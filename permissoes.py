# permissoes.py
#
# Papéis e permissões do PrestServ.
# As permissões são negadas por padrão.


PERFIS = {
    "superadmin": "Superadministrador",
    "admin": "Administrador",
    "secretaria": "Secretaria",
    "porteiro": "Porteiro",
    "consulta": "Consulta",
}


PERMISSOES = {
    # Atendimentos
    "registrar_atendimento": {"superadmin", "admin", "porteiro"},
    "alterar_data_atendimento": {"superadmin", "admin"},
    # Pessoas atendidas
    "consultar_pessoas": {"superadmin", "admin", "secretaria", "porteiro"},
    "cadastrar_pessoas": {"superadmin", "admin", "secretaria"},
    "editar_pessoas": {"superadmin", "admin", "secretaria"},
    "excluir_pessoas": {"superadmin", "admin"},
    "consultar_dados_sensiveis": {"superadmin", "admin", "secretaria"},
    # Relatórios
    "relatorios_gerais": {"superadmin", "admin", "consulta"},
    "relatorios_pessoais": {"superadmin", "admin"},
    "exportar_relatorios": {"superadmin", "admin"},
    # Administração
    "gerenciar_usuarios": {"superadmin"},
    "consultar_logs": {"superadmin"},
    "excluir_logs": {"superadmin"},
    # Backup e restauração
    "gerar_backup": {"superadmin"},
    "restaurar_backup": {"superadmin"},
    # Doações e compras
    "gerenciar_entradas": {"superadmin", "admin", "secretaria"},
    "consultar_fotos": {"superadmin", "admin", "secretaria", "porteiro"},
}


def tem_permissao(perfil, permissao):
    """Verifica se um perfil possui determinada permissão."""

    if perfil not in PERFIS:
        return False

    perfis_autorizados = PERMISSOES.get(permissao, set())

    return perfil in perfis_autorizados


def exigir_permissao(perfil, permissao):
    """Impede operações não autorizadas."""

    if not tem_permissao(perfil, permissao):
        raise PermissionError(f"Permissão negada para a operação: {permissao}")


def exigir_permissao_usuario(conexao, usuario_id, permissao):
    """
    Verifica a permissão consultando o usuário no banco.

    Deve receber a mesma conexão utilizada pela operação
    protegida, preferencialmente dentro de uma transação.
    """

    usuario = conexao.execute(
        """
        SELECT perfil, ativo
        FROM usuarios
        WHERE id = ?
        """,
        (usuario_id,),
    ).fetchone()

    if usuario is None:
        raise PermissionError("Usuário não encontrado.")

    perfil, ativo = usuario

    if not ativo:
        raise PermissionError("Usuário inativo.")

    exigir_permissao(perfil, permissao)

    return perfil
