def test_criar_conta(auth_client):
    response = auth_client.post("/contas", json={"nome": "Carteira", "saldo_inicial": 100.5})
    assert response.status_code == 201
    body = response.json()
    assert body["nome"] == "Carteira"
    assert body["saldo_inicial"] == 100.5
    assert body["ativo"] is True
    assert "id" in body
    assert "criado_em" in body


def test_criar_conta_dados_invalidos(auth_client):
    response = auth_client.post("/contas", json={"saldo_inicial": 100})
    assert response.status_code == 422


def test_listar_contas(auth_client):
    auth_client.post("/contas", json={"nome": "Conta A"})
    auth_client.post("/contas", json={"nome": "Conta B"})

    response = auth_client.get("/contas")
    assert response.status_code == 200
    nomes = {c["nome"] for c in response.json()}
    assert {"Conta A", "Conta B"} <= nomes


def test_obter_conta_existente(auth_client):
    criada = auth_client.post("/contas", json={"nome": "Conta X"}).json()

    response = auth_client.get(f"/contas/{criada['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == criada["id"]


def test_obter_conta_inexistente(auth_client):
    response = auth_client.get("/contas/99999")
    assert response.status_code == 404


def test_atualizar_conta(auth_client):
    criada = auth_client.post("/contas", json={"nome": "Original", "saldo_inicial": 0}).json()

    response = auth_client.put(f"/contas/{criada['id']}", json={"nome": "Atualizada"})
    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == "Atualizada"
    assert body["saldo_inicial"] == 0


def test_remover_conta_e_soft_delete(auth_client):
    criada = auth_client.post("/contas", json={"nome": "Para remover"}).json()
    conta_id = criada["id"]

    response = auth_client.delete(f"/contas/{conta_id}")
    assert response.status_code == 204

    # continua existindo, apenas inativa
    obtida = auth_client.get(f"/contas/{conta_id}?include_inactive=true")
    assert obtida.status_code == 200
    assert obtida.json()["ativo"] is False

    # some da listagem padrão
    listagem_padrao = auth_client.get("/contas").json()
    assert conta_id not in {c["id"] for c in listagem_padrao}

    # aparece com include_inactive=true
    listagem_com_inativas = auth_client.get("/contas?include_inactive=true").json()
    assert conta_id in {c["id"] for c in listagem_com_inativas}


def test_remover_conta_referenciada_por_transacao_nao_apaga_transacao(auth_client):
    conta = auth_client.post("/contas", json={"nome": "Conta com transação"}).json()
    transacao = auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta["id"],
            "tipo": "saida",
            "valor": 50,
            "data": "2026-01-10",
        },
    ).json()

    delete_response = auth_client.delete(f"/contas/{conta['id']}")
    assert delete_response.status_code == 204

    transacao_ainda_existe = auth_client.get(f"/transacoes/{transacao['id']}")
    assert transacao_ainda_existe.status_code == 200
    assert transacao_ainda_existe.json()["conta_id"] == conta["id"]
