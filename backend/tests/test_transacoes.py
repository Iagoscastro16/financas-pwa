from datetime import datetime, timedelta

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


def test_criar_transacao_sem_data_usa_datetime_now(auth_client, conta):
    antes = datetime.now()
    response = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "saida", "valor": 42.5},
    )
    depois = datetime.now()
    assert response.status_code == 201
    data_retornada = datetime.fromisoformat(response.json()["data"])
    assert antes - timedelta(seconds=5) <= data_retornada <= depois + timedelta(seconds=5)


def test_criar_transacao_com_datetime_completo_preserva_horario(auth_client, conta):
    response = auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta["id"],
            "tipo": "saida",
            "valor": 42.5,
            "data": "2026-02-01T15:30:00",
        },
    )
    assert response.status_code == 201
    assert response.json()["data"] == "2026-02-01T15:30:00"


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


def test_listar_transacoes_ordenacao_padrao_e_data_desc(auth_client, conta):
    mais_antiga = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 10, "data": "2026-03-01T08:00:00"},
    ).json()
    mais_recente = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 10, "data": "2026-03-10T08:00:00"},
    ).json()

    response = auth_client.get("/transacoes")
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert ids == [mais_recente["id"], mais_antiga["id"]]


def test_listar_transacoes_ordenar_por_data_asc(auth_client, conta):
    mais_antiga = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 10, "data": "2026-03-01T08:00:00"},
    ).json()
    mais_recente = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 10, "data": "2026-03-10T08:00:00"},
    ).json()

    response = auth_client.get("/transacoes", params={"ordenar_por": "data_asc"})
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert ids == [mais_antiga["id"], mais_recente["id"]]


def test_listar_transacoes_data_desc_com_timestamps_iguais_desempata_por_id(auth_client, conta):
    primeira = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 10, "data": "2026-03-05T12:00:00"},
    ).json()
    segunda = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 10, "data": "2026-03-05T12:00:00"},
    ).json()

    response = auth_client.get("/transacoes")
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert ids == [segunda["id"], primeira["id"]]


def test_listar_transacoes_ordenar_por_categoria(auth_client, conta):
    # Cria a categoria "Uber" antes de "Alimentação" de propósito: se a
    # ordenação estivesse (incorretamente) usando o id da categoria em vez
    # do nome, "Uber" (id menor) apareceria primeiro. Alfabeticamente,
    # "Alimentação" deve vir antes.
    categoria_uber = auth_client.post(
        "/categorias", json={"nome": "Uber", "tipo": "despesa"}
    ).json()
    categoria_alimentacao = auth_client.post(
        "/categorias", json={"nome": "Alimentação", "tipo": "despesa"}
    ).json()

    transacao_uber = auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta["id"],
            "tipo": "saida",
            "valor": 10,
            "data": "2026-03-01",
            "categoria_ids": [categoria_uber["id"]],
        },
    ).json()
    transacao_alimentacao = auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta["id"],
            "tipo": "saida",
            "valor": 10,
            "data": "2026-03-02",
            "categoria_ids": [categoria_alimentacao["id"]],
        },
    ).json()
    transacao_sem_categoria = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "saida", "valor": 10, "data": "2026-03-03"},
    ).json()

    response = auth_client.get("/transacoes", params={"ordenar_por": "categoria"})
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert ids == [
        transacao_alimentacao["id"],
        transacao_uber["id"],
        transacao_sem_categoria["id"],
    ]


def test_listar_transacoes_ordenar_por_categoria_e_case_insensitive(auth_client, conta):
    # Ordenação binária padrão do SQL colocaria "Uber" (maiúscula) antes de
    # "teste" (minúscula); alfabetização A-Z esperada pelo usuário é
    # case-insensitive e deve colocar "teste" primeiro.
    categoria_uber = auth_client.post(
        "/categorias", json={"nome": "Uber", "tipo": "despesa"}
    ).json()
    categoria_teste = auth_client.post(
        "/categorias", json={"nome": "teste", "tipo": "despesa"}
    ).json()

    transacao_uber = auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta["id"],
            "tipo": "saida",
            "valor": 10,
            "data": "2026-03-01",
            "categoria_ids": [categoria_uber["id"]],
        },
    ).json()
    transacao_teste = auth_client.post(
        "/transacoes",
        json={
            "conta_id": conta["id"],
            "tipo": "saida",
            "valor": 10,
            "data": "2026-03-02",
            "categoria_ids": [categoria_teste["id"]],
        },
    ).json()

    response = auth_client.get("/transacoes", params={"ordenar_por": "categoria"})
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert ids == [transacao_teste["id"], transacao_uber["id"]]


def test_listar_transacoes_ordenar_por_invalido_retorna_400(auth_client):
    response = auth_client.get("/transacoes", params={"ordenar_por": "valor_desc"})
    assert response.status_code == 400
    assert "ordenar_por" in response.json()["detail"]


def test_listar_transacoes_ordenar_por_com_mes_ano(auth_client, conta):
    fora_do_mes = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 10, "data": "2026-04-15T08:00:00"},
    ).json()
    antiga = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 10, "data": "2026-03-01T08:00:00"},
    ).json()
    recente = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "entrada", "valor": 10, "data": "2026-03-20T08:00:00"},
    ).json()

    response = auth_client.get(
        "/transacoes", params={"mes_ano": "2026-03", "ordenar_por": "data_asc"}
    )
    assert response.status_code == 200
    body = response.json()
    ids = [t["id"] for t in body]
    assert ids == [antiga["id"], recente["id"]]
    assert fora_do_mes["id"] not in ids


def test_remover_transacao_e_hard_delete(auth_client, conta):
    criada = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "saida", "valor": 5, "data": "2026-02-05"},
    ).json()

    response = auth_client.delete(f"/transacoes/{criada['id']}")
    assert response.status_code == 204

    obtida = auth_client.get(f"/transacoes/{criada['id']}")
    assert obtida.status_code == 404
