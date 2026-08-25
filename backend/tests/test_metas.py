def test_criar_meta(auth_client):
    response = auth_client.post(
        "/metas",
        json={"nome": "Viagem", "valor_alvo": 5000, "prazo": "2026-12-31"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nome"] == "Viagem"
    assert body["valor_alvo"] == 5000
    assert body["valor_atual"] == 0
    assert "id" in body


def test_criar_meta_dados_invalidos(auth_client):
    response = auth_client.post("/metas", json={"nome": "Sem valor alvo"})
    assert response.status_code == 422


def test_criar_meta_valor_alvo_invalido(auth_client):
    response = auth_client.post("/metas", json={"nome": "Valor negativo", "valor_alvo": -10})
    assert response.status_code == 422


def test_listar_metas(auth_client):
    auth_client.post("/metas", json={"nome": "Meta A", "valor_alvo": 1000})
    auth_client.post("/metas", json={"nome": "Meta B", "valor_alvo": 2000})

    response = auth_client.get("/metas")
    assert response.status_code == 200
    nomes = {m["nome"] for m in response.json()}
    assert {"Meta A", "Meta B"} <= nomes


def test_obter_meta_existente(auth_client):
    criada = auth_client.post("/metas", json={"nome": "Meta X", "valor_alvo": 300}).json()

    response = auth_client.get(f"/metas/{criada['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == criada["id"]


def test_obter_meta_inexistente(auth_client):
    response = auth_client.get("/metas/99999")
    assert response.status_code == 404


def test_atualizar_meta(auth_client):
    criada = auth_client.post("/metas", json={"nome": "Original", "valor_alvo": 500}).json()

    response = auth_client.put(f"/metas/{criada['id']}", json={"valor_atual": 100})
    assert response.status_code == 200
    body = response.json()
    assert body["valor_atual"] == 100
    assert body["valor_alvo"] == 500


def test_remover_meta_e_hard_delete(auth_client):
    criada = auth_client.post("/metas", json={"nome": "Remover", "valor_alvo": 100}).json()

    response = auth_client.delete(f"/metas/{criada['id']}")
    assert response.status_code == 204

    obtida = auth_client.get(f"/metas/{criada['id']}")
    assert obtida.status_code == 404
