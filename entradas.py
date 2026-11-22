"""Registro de doações e compras (sem controle de estoque)."""

from datetime import date
from decimal import Decimal, InvalidOperation
import math

from database import conectar, data_atual, registrar_log
from permissoes import exigir_permissao_usuario


_CAMPOS = (
    "data", "tipo", "categoria", "item", "quantidade",
    "unidade", "origem", "valor_centavos",
)


def _validar_data(valor):
    if not isinstance(valor, str):
        raise ValueError("Data inválida: informe AAAA-MM-DD.")
    try:
        data = date.fromisoformat(valor)
    except ValueError:
        raise ValueError("Data inválida: informe AAAA-MM-DD.") from None
    if valor != data.isoformat() or data > date.fromisoformat(data_atual()):
        raise ValueError("Data inválida ou futura.")
    return valor


def _texto(valor, campo, obrigatorio=True):
    if valor is None and not obrigatorio:
        return None
    if not isinstance(valor, str):
        raise ValueError(f"{campo} inválido.")
    valor = valor.strip()
    if not valor:
        if obrigatorio:
            raise ValueError(f"{campo} é obrigatório.")
        return None
    return valor


def _validar_dados(data, tipo, categoria, item, quantidade, unidade,
                   origem, valor_centavos):
    data = _validar_data(data)
    if tipo not in ("doacao", "compra"):
        raise ValueError("Tipo deve ser 'doacao' ou 'compra'.")
    categoria = _texto(categoria, "Categoria")
    item = _texto(item, "Item")
    unidade = _texto(unidade, "Unidade")
    origem = _texto(origem, "Origem", obrigatorio=False)

    if isinstance(quantidade, bool):
        raise ValueError("Quantidade inválida.")
    try:
        numero = Decimal(str(quantidade))
        quantidade = float(numero)
    except (InvalidOperation, TypeError, ValueError, OverflowError):
        raise ValueError("Quantidade inválida.") from None
    if not numero.is_finite() or not math.isfinite(quantidade) or quantidade <= 0:
        raise ValueError("Quantidade deve ser um número positivo e finito.")

    if valor_centavos is not None and (
        type(valor_centavos) is not int or valor_centavos < 0
    ):
        raise ValueError("Valor deve ser um inteiro em centavos ou None.")

    return {
        "data": data,
        "tipo": tipo,
        "categoria": categoria,
        "item": item,
        "quantidade": quantidade,
        "unidade": unidade,
        "origem": origem,
        "valor_centavos": valor_centavos,
    }


def _detalhes_log(dados):
    """Evita gravar a identificação da origem/doador nos logs."""
    return {
        chave: valor for chave, valor in dados.items()
        if chave != "origem"
    } | {"origem_informada": bool(dados["origem"])}


def registrar_entrada(data, tipo, categoria, item, quantidade, unidade,
                      origem=None, valor_centavos=None, *, ator_id):
    """Registra uma entrada e o respectivo log numa transação."""
    dados = _validar_dados(data, tipo, categoria, item, quantidade,
                          unidade, origem, valor_centavos)

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")
        exigir_permissao_usuario(conexao, ator_id, "gerenciar_entradas")
        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?", (ator_id,)
        ).fetchone()

        cursor = conexao.execute(
            """
            INSERT INTO entradas
                (data, tipo, categoria, item, quantidade, unidade,
                 origem, valor_centavos, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*dados.values(), ator_id),
        )
        entrada_id = cursor.lastrowid
        registrar_log(
            conexao,
            acao="criar_entrada",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="entradas",
            entidade_id=entrada_id,
            detalhes=_detalhes_log(dados),
        )
        return entrada_id


def listar_entradas(inicio=None, fim=None, tipo=None, categoria=None, *, ator_id):
    """Consulta entradas com filtros opcionais; exige permissão."""
    if inicio is not None:
        inicio = _validar_data(inicio)
    if fim is not None:
        fim = _validar_data(fim)
    if inicio and fim and inicio > fim:
        raise ValueError("A data inicial não pode superar a final.")
    if tipo is not None and tipo not in ("doacao", "compra"):
        raise ValueError("Tipo inválido.")
    if categoria is not None:
        categoria = _texto(categoria, "Categoria")

    condicoes = []
    parametros = []
    if inicio:
        condicoes.append("e.data >= ?")
        parametros.append(inicio)
    if fim:
        condicoes.append("e.data <= ?")
        parametros.append(fim)
    if tipo:
        condicoes.append("e.tipo = ?")
        parametros.append(tipo)
    if categoria:
        condicoes.append("e.categoria = ? COLLATE NOCASE")
        parametros.append(categoria)

    where = "WHERE " + " AND ".join(condicoes) if condicoes else ""

    with conectar() as conexao:
        exigir_permissao_usuario(conexao, ator_id, "gerenciar_entradas")
        registros = conexao.execute(
            f"""
            SELECT e.*, u.nome AS registrado_por
            FROM entradas e
            JOIN usuarios u ON u.id = e.usuario_id
            {where}
            ORDER BY e.data DESC, e.id DESC
            """,
            parametros,
        ).fetchall()
    return [dict(registro) for registro in registros]


def atualizar_entrada(entrada_id, data, tipo, categoria, item, quantidade,
                       unidade, origem=None, valor_centavos=None, *, ator_id):
    """Atualiza uma entrada; registra somente mudanças efetivas."""
    if type(entrada_id) is not int or entrada_id <= 0:
        raise ValueError("Identificador de entrada inválido.")
    dados = _validar_dados(data, tipo, categoria, item, quantidade,
                          unidade, origem, valor_centavos)

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")
        exigir_permissao_usuario(conexao, ator_id, "gerenciar_entradas")
        anterior = conexao.execute(
            "SELECT * FROM entradas WHERE id = ?", (entrada_id,)
        ).fetchone()
        if anterior is None:
            raise ValueError("Entrada não encontrada.")

        mudancas = {}
        for campo, novo in dados.items():
            antigo = anterior[campo]
            if antigo != novo:
                if campo == "origem":
                    mudancas[campo] = {
                        "antes_preenchido": bool(antigo),
                        "depois_preenchido": bool(novo),
                    }
                else:
                    mudancas[campo] = {"antes": antigo, "depois": novo}

        if not mudancas:
            return False

        conexao.execute(
            """
            UPDATE entradas SET
                data = ?, tipo = ?, categoria = ?, item = ?,
                quantidade = ?, unidade = ?, origem = ?, valor_centavos = ?
            WHERE id = ?
            """,
            (*dados.values(), entrada_id),
        )
        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?", (ator_id,)
        ).fetchone()
        registrar_log(
            conexao,
            acao="atualizar_entrada",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="entradas",
            entidade_id=entrada_id,
            detalhes={"alteracoes": mudancas},
        )
        return True


def excluir_entrada(entrada_id, *, ator_id):
    """Exclui uma entrada; preserva histórico da operação nos logs."""
    if type(entrada_id) is not int or entrada_id <= 0:
        raise ValueError("Identificador de entrada inválido.")

    with conectar() as conexao:
        conexao.execute("BEGIN IMMEDIATE")
        exigir_permissao_usuario(conexao, ator_id, "gerenciar_entradas")
        anterior = conexao.execute(
            "SELECT * FROM entradas WHERE id = ?", (entrada_id,)
        ).fetchone()
        if anterior is None:
            raise ValueError("Entrada não encontrada.")

        conexao.execute("DELETE FROM entradas WHERE id = ?", (entrada_id,))
        operador = conexao.execute(
            "SELECT login FROM usuarios WHERE id = ?", (ator_id,)
        ).fetchone()
        registrar_log(
            conexao,
            acao="excluir_entrada",
            usuario_id=ator_id,
            usuario_login=operador["login"],
            entidade="entradas",
            entidade_id=entrada_id,
            detalhes=_detalhes_log({chave: anterior[chave] for chave in _CAMPOS}),
        )
