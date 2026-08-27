def _criar_conta(auth_client, nome="Conta", saldo_inicial=0):
    return auth_client.post("/contas", json={"nome": nome, "saldo_inicial": saldo_inicial}).json()


def _criar_categoria(auth_client, nome, tipo="despesa"):
    return auth_client.post("/categorias", json={"nome": nome, "tipo": tipo}).json()


def _criar_transacao(auth_client, conta_id, tipo, valor, data, categoria_ids=None):
    return auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta_id,
            "tipo": tipo,
            "valor": valor,
            "data": data,
            "categoria_ids": categoria_ids or [],
        },
    ).json()


def test_resumo_mensal_com_transacoes(auth_client):
    conta = _criar_conta(auth_client, saldo_inicial=100)
    _criar_transacao(auth_client, conta["id"], "entrada", 500, "2026-03-05")
    _criar_transacao(auth_client, conta["id"], "saida", 200, "2026-03-10")

    response = auth_client.get("/resumo/mensal", params={"mes_ano": "2026-03"})
    assert response.status_code == 200
    body = response.json()
    assert body["mes_ano"] == "2026-03"
    assert body["total_entradas"] == 500
    assert body["total_saidas"] == 200
    assert body["saldo_periodo"] == 300
    assert body["saldo_total_contas"] == 400  # 100 + 500 - 200


def test_resumo_mensal_sem_transacoes_retorna_zeros(auth_client):
    conta = _criar_conta(auth_client, saldo_inicial=100)
    _criar_transacao(auth_client, conta["id"], "entrada", 500, "2026-03-05")

    response = auth_client.get("/resumo/mensal", params={"mes_ano": "2026-04"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_entradas"] == 0
    assert body["total_saidas"] == 0
    assert body["saldo_periodo"] == 0
    # saldo_total_contas reflete o saldo real da conta, não é zerado por mês.
    assert body["saldo_total_contas"] == 600


def test_resumo_mensal_default_mes_atual_nao_falha(auth_client):
    response = auth_client.get("/resumo/mensal")
    assert response.status_code == 200


def test_resumo_mensal_exclui_conta_inativa_do_saldo_total(auth_client):
    conta_ativa = _criar_conta(auth_client, saldo_inicial=100)
    conta_inativa = _criar_conta(auth_client, saldo_inicial=1000)
    _criar_transacao(auth_client, conta_ativa["id"], "entrada", 50, "2026-03-01")
    _criar_transacao(auth_client, conta_inativa["id"], "entrada", 999, "2026-03-01")

    auth_client.delete(f"/contas/{conta_inativa['id']}")

    response = auth_client.get("/resumo/mensal", params={"mes_ano": "2026-03"})
    body = response.json()
    # total_entradas do mês inclui a transação da conta inativa (soft delete
    # não apaga o histórico), mas saldo_total_contas só soma contas ativas.
    assert body["total_entradas"] == 1049
    assert body["saldo_total_contas"] == 150


def test_resumo_categorias_agrupamento_e_sem_categoria(auth_client):
    conta = _criar_conta(auth_client)
    cat_a = _criar_categoria(auth_client, "Mercado")
    cat_b = _criar_categoria(auth_client, "Lazer")

    _criar_transacao(auth_client, conta["id"], "saida", 100, "2026-05-01", [cat_a["id"]])
    _criar_transacao(auth_client, conta["id"], "saida", 60, "2026-05-02", [cat_a["id"], cat_b["id"]])
    _criar_transacao(auth_client, conta["id"], "saida", 40, "2026-05-03", [])
    # entrada não deve contar nesta agregação (só saida)
    _criar_transacao(auth_client, conta["id"], "entrada", 999, "2026-05-04", [cat_a["id"]])

    response = auth_client.get("/resumo/categorias", params={"mes_ano": "2026-05"})
    assert response.status_code == 200
    itens = {item["nome"]: item for item in response.json()}

    assert itens["Mercado"]["total"] == 130  # 100 + 60/2
    assert itens["Lazer"]["total"] == 30  # 60/2
    assert itens["Sem categoria"]["total"] == 40
    assert itens["Sem categoria"]["categoria_id"] is None

    soma_percentuais = sum(item["percentual"] for item in itens.values())
    assert abs(soma_percentuais - 100) < 0.01

    assert itens["Mercado"]["percentual"] == 65.0
    assert itens["Lazer"]["percentual"] == 15.0
    assert itens["Sem categoria"]["percentual"] == 20.0


def test_resumo_categorias_sem_saidas_no_mes(auth_client):
    conta = _criar_conta(auth_client)
    _criar_transacao(auth_client, conta["id"], "entrada", 100, "2026-06-01")

    response = auth_client.get("/resumo/categorias", params={"mes_ano": "2026-06"})
    assert response.status_code == 200
    assert response.json() == []


def test_resumo_categorias_total_modo_liquido(auth_client):
    auth_client.put("/configuracao/total_categoria_separado", json={"valor": False})

    conta = _criar_conta(auth_client)
    conta_inativa = _criar_conta(auth_client)
    categoria_x = _criar_categoria(auth_client, "Salario", tipo="receita")
    categoria_y = _criar_categoria(auth_client, "Transporte")

    _criar_transacao(auth_client, conta["id"], "entrada", 100, "2026-01-01", [categoria_x["id"]])
    _criar_transacao(auth_client, conta["id"], "saida", 40, "2026-01-02", [categoria_x["id"]])
    _criar_transacao(auth_client, conta["id"], "entrada", 50, "2026-01-03", [categoria_y["id"]])
    _criar_transacao(auth_client, conta["id"], "saida", 20, "2026-01-04", [categoria_y["id"]])
    # transação em conta soft-deletada: histórico ainda deve contar
    _criar_transacao(auth_client, conta_inativa["id"], "entrada", 10, "2026-01-05", [categoria_x["id"]])
    auth_client.delete(f"/contas/{conta_inativa['id']}")

    # soft-delete da categoria não deve remover seu histórico nem seu nome
    auth_client.delete(f"/categorias/{categoria_y['id']}")

    response = auth_client.get("/resumo/categorias/total")
    assert response.status_code == 200
    itens = {item["nome"]: item for item in response.json()}

    assert itens["Salario"]["total"] == 70  # 100 + 10 - 40
    assert itens["Transporte"]["total"] == 30  # 50 - 20
    assert "total_entrada" not in itens["Salario"]


def test_resumo_categorias_total_modo_separado(auth_client):
    auth_client.put("/configuracao/total_categoria_separado", json={"valor": True})

    conta = _criar_conta(auth_client)
    categoria_x = _criar_categoria(auth_client, "Salario", tipo="receita")

    _criar_transacao(auth_client, conta["id"], "entrada", 100, "2026-01-01", [categoria_x["id"]])
    _criar_transacao(auth_client, conta["id"], "saida", 40, "2026-01-02", [categoria_x["id"]])

    response = auth_client.get("/resumo/categorias/total")
    assert response.status_code == 200
    itens = {item["nome"]: item for item in response.json()}

    assert itens["Salario"]["total_entrada"] == 100
    assert itens["Salario"]["total_saida"] == 40
    assert "total" not in itens["Salario"]


def test_resumo_comparativo_aumento_e_queda(auth_client):
    conta = _criar_conta(auth_client)
    _criar_transacao(auth_client, conta["id"], "entrada", 100, "2026-01-15")
    _criar_transacao(auth_client, conta["id"], "saida", 50, "2026-01-16")
    _criar_transacao(auth_client, conta["id"], "entrada", 150, "2026-02-15")
    _criar_transacao(auth_client, conta["id"], "saida", 25, "2026-02-16")

    response = auth_client.get(
        "/resumo/comparativo", params={"mes1": "2026-01", "mes2": "2026-02"}
    )
    assert response.status_code == 200
    body = response.json()

    assert body["mes1"]["total_entradas"] == 100
    assert body["mes2"]["total_entradas"] == 150
    assert body["variacao_percentual"]["total_entradas"] == 50.0

    assert body["mes1"]["total_saidas"] == 50
    assert body["mes2"]["total_saidas"] == 25
    assert body["variacao_percentual"]["total_saidas"] == -50.0


def test_resumo_comparativo_requer_ambos_meses(auth_client):
    response = auth_client.get("/resumo/comparativo", params={"mes1": "2026-01"})
    assert response.status_code == 422


def test_resumo_comparativo_base_zero_retorna_variacao_nula(auth_client):
    conta = _criar_conta(auth_client)
    # mes1 (2026-07) fica sem nenhuma transação: base zero para ambos os campos.
    _criar_transacao(auth_client, conta["id"], "entrada", 200, "2026-08-01")
    _criar_transacao(auth_client, conta["id"], "saida", 80, "2026-08-02")

    response = auth_client.get(
        "/resumo/comparativo", params={"mes1": "2026-07", "mes2": "2026-08"}
    )
    assert response.status_code == 200
    body = response.json()

    assert body["mes1"]["total_entradas"] == 0
    assert body["mes1"]["total_saidas"] == 0
    # Base zero: variação percentual não é calculável, deve ser null, não 0.
    assert body["variacao_percentual"]["total_entradas"] is None
    assert body["variacao_percentual"]["total_saidas"] is None
