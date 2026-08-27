import pytest


@pytest.fixture()
def conta(auth_client):
    return auth_client.post("/contas", json={"nome": "Conta de teste"}).json()


@pytest.fixture()
def categoria(auth_client):
    return auth_client.post(
        "/categorias", json={"nome": "Categoria de teste", "tipo": "despesa"}
    ).json()


def test_criar_transacao(auth_client, conta):
    response = auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta["id"],
            "tipo": "saida",
            "valor": 42.5,
            "data": "2026-02-01",
            "descricao": "Compra",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["conta_id"] == conta["id"]
    assert body["valor"] == 42.5
    assert body["descricao"] == "Compra"
    assert body["categorias"] == []
    assert "id" in body


def test_criar_transacao_com_categorias_retorna_categorias_aninhadas(
    auth_client, conta, categoria
):
    response = auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta["id"],
            "tipo": "saida",
            "valor": 10,
            "data": "2026-02-02",
            "categoria_ids": [categoria["id"]],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["categorias"]) == 1
    assert body["categorias"][0]["id"] == categoria["id"]
    assert body["categorias"][0]["nome"] == categoria["nome"]


def test_criar_transacao_dados_invalidos(auth_client, conta):
    response = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "saida", "valor": -5, "data": "2026-02-01"},
    )
    assert response.status_code == 422


def test_criar_transacao_conta_inexistente(auth_client):
    response = auth_client.post(
        "/transacoes",
        json={"conta_id": 99999, "tipo": "saida", "valor": 10, "data": "2026-02-01"},
    )
    assert response.status_code == 400


def test_listar_transacoes(auth_client, conta):
    auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 100, "data": "2026-02-03"},
    )

    response = auth_client.get("/transacoes")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_obter_transacao_existente(auth_client, conta):
    criada = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 20, "data": "2026-02-04"},
    ).json()

    response = auth_client.get(f"/transacoes/{criada['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == criada["id"]


def test_obter_transacao_inexistente(auth_client):
    response = auth_client.get("/transacoes/99999")
    assert response.status_code == 404


def test_atualizar_transacao(auth_client, conta):
    criada = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 20, "data": "2026-02-04"},
    ).json()

    response = auth_client.put(f"/transacoes/{criada['id']}", json={"valor": 99.9})
    assert response.status_code == 200
    body = response.json()
    assert body["valor"] == 99.9


def test_listar_transacoes_filtra_por_mes_ano(auth_client, conta):
    auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 100, "data": "2026-03-10"},
    )
    auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "saida", "valor": 30, "data": "2026-03-20"},
    )
    fora_do_mes = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "saida", "valor": 999, "data": "2026-04-01"},
    ).json()

    response = auth_client.get("/transacoes", params={"mes_ano": "2026-03"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    ids_retornados = {t["id"] for t in body}
    assert fora_do_mes["id"] not in ids_retornados
    assert all(t["data"].startswith("2026-03") for t in body)


def test_listar_transacoes_mes_ano_sem_transacoes_retorna_lista_vazia(auth_client, conta):
    auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 100, "data": "2026-03-10"},
    )

    response = auth_client.get("/transacoes", params={"mes_ano": "2026-05"})
    assert response.status_code == 200
    assert response.json() == []


def test_listar_transacoes_sem_filtro_retorna_todas(auth_client, conta):
    auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 100, "data": "2026-03-10"},
    )
    auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "saida", "valor": 30, "data": "2026-04-01"},
    )

    response = auth_client.get("/transacoes")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_listar_transacoes_mes_ano_formato_invalido(auth_client):
    response = auth_client.get("/transacoes", params={"mes_ano": "invalido"})
    assert response.status_code == 400


def test_remover_transacao_e_hard_delete(auth_client, conta):
    criada = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "saida", "valor": 5, "data": "2026-02-05"},
    ).json()

    response = auth_client.delete(f"/transacoes/{criada['id']}")
    assert response.status_code == 204

    obtida = auth_client.get(f"/transacoes/{criada['id']}")
    assert obtida.status_code == 404
