import os
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as pasta:
    os.environ["PRESTSERV_DB_PATH"] = str(Path(pasta) / "temp.db")
    from inicializar_banco import inicializar_banco
    from auth import criar_usuario
    from database import conectar, data_atual
    from entradas import (
        registrar_entrada,
        listar_entradas,
        atualizar_entrada,
        excluir_entrada,
    )

    inicializar_banco()
    super_id = criar_usuario("Admin", "admin", "senha0000", "superadmin")
    secretaria_id = criar_usuario(
        "Sec", "sec", "senha0000", "secretaria", ator_id=super_id
    )
    porteiro_id = criar_usuario(
        "Port", "port", "senha0000", "porteiro", ator_id=super_id
    )
    hoje = data_atual()
    eid = registrar_entrada(
        hoje,
        "doacao",
        "Alimentos",
        "Arroz",
        2.5,
        "kg",
        "João",
        None,
        ator_id=secretaria_id,
    )
    eid2 = registrar_entrada(
        hoje, "compra", "Higiene", "Sabão", 3, "un", "Mercado", 1250, ator_id=super_id
    )
    lista = listar_entradas(ator_id=secretaria_id)
    assert len(lista) == 2 and lista[0]["id"] == eid2
    assert lista[1]["quantidade"] == 2.5
    assert [e["id"] for e in listar_entradas(tipo="doacao", ator_id=super_id)] == [eid]
    assert [
        e["id"] for e in listar_entradas(categoria="alimentos", ator_id=super_id)
    ] == [eid]
    assert [
        e["id"] for e in listar_entradas(inicio=hoje, fim=hoje, ator_id=super_id)
    ] == [eid2, eid]
    assert atualizar_entrada(
        eid,
        hoje,
        "doacao",
        "Alimentos",
        "Arroz",
        3.75,
        "kg",
        "João",
        None,
        ator_id=secretaria_id,
    )
    assert not atualizar_entrada(
        eid,
        hoje,
        "doacao",
        "Alimentos",
        "Arroz",
        3.75,
        "kg",
        "João",
        None,
        ator_id=secretaria_id,
    )
    assert (
        next(e for e in listar_entradas(ator_id=super_id) if e["id"] == eid)[
            "quantidade"
        ]
        == 3.75
    )
    for bad in (0, -1, float("nan"), float("inf"), True, "sdf"):
        try:
            registrar_entrada(
                hoje, "doacao", "Alimentos", "Item", bad, "kg", ator_id=super_id
            )
        except ValueError:
            pass
        else:
            raise AssertionError(str(bad))
    for bad in (1.2, "120", -1, True):
        try:
            registrar_entrada(
                hoje,
                "compra",
                "Alimentos",
                "Item",
                1,
                "kg",
                valor_centavos=bad,
                ator_id=super_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(str(bad))
    for f in (
        lambda: listar_entradas(ator_id=porteiro_id),
        lambda: registrar_entrada(
            hoje, "doacao", "A", "B", 1, "kg", ator_id=porteiro_id
        ),
        lambda: atualizar_entrada(
            eid, hoje, "doacao", "A", "B", 1, "kg", ator_id=porteiro_id
        ),
        lambda: excluir_entrada(eid, ator_id=porteiro_id),
    ):
        try:
            f()
        except PermissionError:
            pass
        else:
            raise AssertionError("permission failure")
    excluir_entrada(eid, ator_id=super_id)
    assert [e["id"] for e in listar_entradas(ator_id=super_id)] == [eid2]
    with conectar() as c:
        logs = c.execute(
            "SELECT acao,detalhes_json FROM logs WHERE entidade='entradas' ORDER BY id"
        ).fetchall()
        assert [r["acao"] for r in logs] == [
            "criar_entrada",
            "criar_entrada",
            "atualizar_entrada",
            "excluir_entrada",
        ]
        assert all("João" not in r["detalhes_json"] for r in logs)
        assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    print("Cadastro/listagem com filtros: OK")
    print("Edição, sem logs redundantes: OK")
    print("Exclusão com auditoria: OK")
    print("Validação e permissões: OK")
    print("Integridade SQLite: OK")
print("TESTES: OK")
