def test_criar_categoria(auth_client):
    response = auth_client.post("/categorias", json={"nome": "Mercado", "tipo": "despesa"})
    assert response.status_code == 201
    body = response.json()
    assert body["nome"] == "Mercado"
    assert body["tipo"] == "despesa"
    assert body["ativo"] is True
    assert "id" in body


def test_criar_categoria_dados_invalidos(auth_client):
    response = auth_client.post("/categorias", json={"nome": "Sem tipo"})
    assert response.status_code == 422


def test_criar_categoria_tipo_invalido(auth_client):
    response = auth_client.post("/categorias", json={"nome": "Tipo ruim", "tipo": "invalido"})
    assert response.status_code == 422


def test_listar_categorias(auth_client):
    auth_client.post("/categorias", json={"nome": "Salário", "tipo": "receita"})
    auth_client.post("/categorias", json={"nome": "Lazer", "tipo": "despesa"})

    response = auth_client.get("/categorias")
    assert response.status_code == 200
    nomes = {c["nome"] for c in response.json()}
    assert {"Salário", "Lazer"} <= nomes


def test_obter_categoria_existente(auth_client):
    criada = auth_client.post("/categorias", json={"nome": "Saúde", "tipo": "despesa"}).json()

    response = auth_client.get(f"/categorias/{criada['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == criada["id"]


def test_obter_categoria_inexistente(auth_client):
    response = auth_client.get("/categorias/99999")
    assert response.status_code == 404


def test_atualizar_categoria(auth_client):
    criada = auth_client.post("/categorias", json={"nome": "Original", "tipo": "despesa"}).json()

    response = auth_client.put(f"/categorias/{criada['id']}", json={"nome": "Atualizada"})
    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == "Atualizada"
    assert body["tipo"] == "despesa"


def test_remover_categoria_e_soft_delete(auth_client):
    criada = auth_client.post("/categorias", json={"nome": "Remover", "tipo": "despesa"}).json()
    categoria_id = criada["id"]

    response = auth_client.delete(f"/categorias/{categoria_id}")
    assert response.status_code == 204

    obtida = auth_client.get(f"/categorias/{categoria_id}?include_inactive=true")
    assert obtida.status_code == 200
    assert obtida.json()["ativo"] is False

    listagem_padrao = auth_client.get("/categorias").json()
    assert categoria_id not in {c["id"] for c in listagem_padrao}

    listagem_com_inativas = auth_client.get("/categorias?include_inactive=true").json()
    assert categoria_id in {c["id"] for c in listagem_com_inativas}


def test_remover_categoria_referenciada_por_transacao_nao_apaga_transacao(auth_client):
    conta = auth_client.post("/contas", json={"nome": "Conta"}).json()
    categoria = auth_client.post(
        "/categorias", json={"nome": "Categoria referenciada", "tipo": "despesa"}
    ).json()
    transacao = auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta["id"],
            "tipo": "saida",
            "valor": 30,
            "data": "2026-01-15",
            "categoria_ids": [categoria["id"]],
        },
    ).json()

    delete_response = auth_client.delete(f"/categorias/{categoria['id']}")
    assert delete_response.status_code == 204

    transacao_ainda_existe = auth_client.get(f"/transacoes/{transacao['id']}")
    assert transacao_ainda_existe.status_code == 200
    categorias_ids = {c["id"] for c in transacao_ainda_existe.json()["categorias"]}
    assert categoria["id"] in categorias_ids
