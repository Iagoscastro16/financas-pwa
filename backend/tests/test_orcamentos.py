import pytest


@pytest.fixture()
def categoria(auth_client):
    return auth_client.post(
        "/categorias", json={"nome": "Categoria orçamento", "tipo": "despesa"}
    ).json()


def test_criar_orcamento(auth_client, categoria):
    response = auth_client.post(
        "/orcamentos",
        json={"categoria_id": categoria["id"], "mes_ano": "2026-03", "valor_maximo": 500},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["categoria_id"] == categoria["id"]
    assert body["mes_ano"] == "2026-03"
    assert body["valor_maximo"] == 500
    assert "id" in body


def test_criar_orcamento_dados_invalidos(auth_client, categoria):
    response = auth_client.post(
        "/orcamentos",
        json={"categoria_id": categoria["id"], "mes_ano": "mes-invalido", "valor_maximo": 500},
    )
    assert response.status_code == 422


def test_criar_orcamento_categoria_inexistente(auth_client):
    response = auth_client.post(
        "/orcamentos",
        json={"categoria_id": 99999, "mes_ano": "2026-03", "valor_maximo": 500},
    )
    assert response.status_code == 400


def test_listar_orcamentos(auth_client, categoria):
    auth_client.post(
        "/orcamentos",
        json={"categoria_id": categoria["id"], "mes_ano": "2026-04", "valor_maximo": 200},
    )

    response = auth_client.get("/orcamentos")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_obter_orcamento_existente(auth_client, categoria):
    criado = auth_client.post(
        "/orcamentos",
        json={"categoria_id": categoria["id"], "mes_ano": "2026-05", "valor_maximo": 300},
    ).json()

    response = auth_client.get(f"/orcamentos/{criado['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == criado["id"]


def test_obter_orcamento_inexistente(auth_client):
    response = auth_client.get("/orcamentos/99999")
    assert response.status_code == 404


def test_atualizar_orcamento(auth_client, categoria):
    criado = auth_client.post(
        "/orcamentos",
        json={"categoria_id": categoria["id"], "mes_ano": "2026-06", "valor_maximo": 100},
    ).json()

    response = auth_client.put(f"/orcamentos/{criado['id']}", json={"valor_maximo": 250})
    assert response.status_code == 200
    assert response.json()["valor_maximo"] == 250


def test_remover_orcamento_e_hard_delete(auth_client, categoria):
    criado = auth_client.post(
        "/orcamentos",
        json={"categoria_id": categoria["id"], "mes_ano": "2026-07", "valor_maximo": 150},
    ).json()

    response = auth_client.delete(f"/orcamentos/{criado['id']}")
    assert response.status_code == 204

    obtido = auth_client.get(f"/orcamentos/{criado['id']}")
    assert obtido.status_code == 404
