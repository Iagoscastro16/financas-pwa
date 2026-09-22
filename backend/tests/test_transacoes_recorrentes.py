import calendar
from datetime import date, timedelta

import pytest


@pytest.fixture()
def conta(auth_client):
    return auth_client.post("/contas", json={"nome": "Conta de teste"}).json()


@pytest.fixture()
def categoria(auth_client):
    return auth_client.post(
        "/categorias", json={"nome": "Categoria de teste", "tipo": "despesa"}
    ).json()


def _payload_base(conta, **overrides):
    dados = {
        "nome": "Aluguel",
        "valor": 1200,
        "tipo": "saida",
        "conta_id": conta["id"],
        "dia_mes": 10,
        "data_inicio": "2020-01-01",
    }
    dados.update(overrides)
    return dados


def test_criar_transacao_recorrente(auth_client, conta, categoria):
    response = auth_client.post(
        "/transacoes-recorrentes",
        json=_payload_base(conta, categoria_ids=[categoria["id"]]),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nome"] == "Aluguel"
    assert body["valor"] == 1200
    assert body["ativo"] is True
    assert [c["id"] for c in body["categorias"]] == [categoria["id"]]
    assert "id" in body


def test_criar_transacao_recorrente_dia_mes_invalido(auth_client, conta):
    response = auth_client.post(
        "/transacoes-recorrentes", json=_payload_base(conta, dia_mes=32)
    )
    assert response.status_code == 422

    response = auth_client.post(
        "/transacoes-recorrentes", json=_payload_base(conta, dia_mes=0)
    )
    assert response.status_code == 422


def test_criar_transacao_recorrente_conta_inexistente(auth_client, conta):
    response = auth_client.post(
        "/transacoes-recorrentes", json=_payload_base(conta, conta_id=99999)
    )
    assert response.status_code == 400


def test_criar_transacao_recorrente_categoria_inexistente(auth_client, conta):
    response = auth_client.post(
        "/transacoes-recorrentes", json=_payload_base(conta, categoria_ids=[99999])
    )
    assert response.status_code == 400


def test_listar_transacoes_recorrentes(auth_client, conta):
    auth_client.post("/transacoes-recorrentes", json=_payload_base(conta, nome="A"))
    auth_client.post("/transacoes-recorrentes", json=_payload_base(conta, nome="B"))

    response = auth_client.get("/transacoes-recorrentes")
    assert response.status_code == 200
    nomes = {r["nome"] for r in response.json()}
    assert {"A", "B"} <= nomes


def test_obter_transacao_recorrente_existente(auth_client, conta):
    criada = auth_client.post("/transacoes-recorrentes", json=_payload_base(conta)).json()

    response = auth_client.get(f"/transacoes-recorrentes/{criada['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == criada["id"]


def test_obter_transacao_recorrente_inexistente(auth_client):
    response = auth_client.get("/transacoes-recorrentes/99999")
    assert response.status_code == 404


def test_atualizar_transacao_recorrente(auth_client, conta, categoria):
    criada = auth_client.post("/transacoes-recorrentes", json=_payload_base(conta)).json()

    response = auth_client.put(
        f"/transacoes-recorrentes/{criada['id']}",
        json={
            "nome": "Aluguel reajustado",
            "valor": 1350,
            "dia_mes": 5,
            "data_fim": "2027-12-31",
            "categoria_ids": [categoria["id"]],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == "Aluguel reajustado"
    assert body["valor"] == 1350
    assert body["dia_mes"] == 5
    assert body["data_fim"] == "2027-12-31"
    assert [c["id"] for c in body["categorias"]] == [categoria["id"]]
    # campos que definem a regra em si não fazem parte do update
    assert body["conta_id"] == conta["id"]
    assert body["tipo"] == "saida"


def test_editar_regra_nao_altera_transacao_ja_gerada(auth_client, conta):
    hoje = date.today()
    criada = auth_client.post(
        "/transacoes-recorrentes", json=_payload_base(conta, dia_mes=hoje.day)
    ).json()
    transacao_gerada = auth_client.get(
        "/transacoes", params={"apenas_recorrentes": True}
    ).json()[0]

    auth_client.put(
        f"/transacoes-recorrentes/{criada['id']}",
        json={"nome": "Nome novo", "valor": 9999},
    )

    transacao_apos_edicao = auth_client.get(f"/transacoes/{transacao_gerada['id']}").json()
    assert transacao_apos_edicao["descricao"] == transacao_gerada["descricao"]
    assert transacao_apos_edicao["valor"] == transacao_gerada["valor"]


def test_remover_transacao_recorrente_e_soft_delete(auth_client, conta):
    criada = auth_client.post("/transacoes-recorrentes", json=_payload_base(conta)).json()

    response = auth_client.delete(f"/transacoes-recorrentes/{criada['id']}")
    assert response.status_code == 204

    obtida = auth_client.get(
        f"/transacoes-recorrentes/{criada['id']}?include_inactive=true"
    )
    assert obtida.status_code == 200
    assert obtida.json()["ativo"] is False

    listagem_padrao = auth_client.get("/transacoes-recorrentes").json()
    assert criada["id"] not in {r["id"] for r in listagem_padrao}

    listagem_com_inativas = auth_client.get(
        "/transacoes-recorrentes?include_inactive=true"
    ).json()
    assert criada["id"] in {r["id"] for r in listagem_com_inativas}


def test_desativar_regra_preserva_transacao_ja_gerada_sem_cascata(auth_client, conta):
    hoje = date.today()
    criada = auth_client.post(
        "/transacoes-recorrentes", json=_payload_base(conta, dia_mes=hoje.day)
    ).json()
    transacao_gerada = auth_client.get(
        "/transacoes", params={"apenas_recorrentes": True}
    ).json()[0]

    delete_response = auth_client.delete(f"/transacoes-recorrentes/{criada['id']}")
    assert delete_response.status_code == 204

    ainda_existe = auth_client.get(f"/transacoes/{transacao_gerada['id']}")
    assert ainda_existe.status_code == 200
    assert ainda_existe.json()["recorrencia_id"] == criada["id"]


def test_backfill_dia_de_hoje_gera_transacao_imediatamente(auth_client, conta):
    hoje = date.today()
    response = auth_client.post(
        "/transacoes-recorrentes", json=_payload_base(conta, nome="Assinatura", dia_mes=hoje.day)
    )
    assert response.status_code == 201
    regra = response.json()
    assert regra["ultima_geracao"] == hoje.isoformat()

    transacoes = auth_client.get("/transacoes", params={"apenas_recorrentes": True}).json()
    assert len(transacoes) == 1
    assert transacoes[0]["recorrencia_id"] == regra["id"]
    assert transacoes[0]["descricao"] == "Assinatura"
    assert transacoes[0]["conta_id"] == conta["id"]


def test_backfill_dia_futuro_no_mes_nao_gera_ainda(auth_client, conta):
    hoje = date.today()
    ultimo_dia_do_mes = calendar.monthrange(hoje.year, hoje.month)[1]
    if hoje.day >= ultimo_dia_do_mes:
        pytest.skip("hoje já é o último dia do mês: não há dia futuro representável neste mês")

    response = auth_client.post(
        "/transacoes-recorrentes", json=_payload_base(conta, dia_mes=hoje.day + 1)
    )
    assert response.status_code == 201
    regra = response.json()
    assert regra["ultima_geracao"] is None

    transacoes = auth_client.get("/transacoes", params={"apenas_recorrentes": True}).json()
    assert transacoes == []


def test_data_fim_no_passado_impede_geracao_na_criacao(auth_client, conta):
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    response = auth_client.post(
        "/transacoes-recorrentes",
        json=_payload_base(conta, dia_mes=hoje.day, data_fim=ontem.isoformat()),
    )
    assert response.status_code == 201
    regra = response.json()
    assert regra["ultima_geracao"] is None

    transacoes = auth_client.get("/transacoes", params={"apenas_recorrentes": True}).json()
    assert transacoes == []


def test_apenas_recorrentes_filtra_transacoes(auth_client, conta):
    hoje = date.today()
    auth_client.post(
        "/transacoes-recorrentes", json=_payload_base(conta, dia_mes=hoje.day)
    )
    avulsa = auth_client.post(
        "/transacoes",
        json={"conta_id": conta["id"], "tipo": "saida", "valor": 10, "data": "2026-01-05"},
    ).json()

    apenas_recorrentes = auth_client.get(
        "/transacoes", params={"apenas_recorrentes": True}
    ).json()
    assert all(t["recorrencia_id"] is not None for t in apenas_recorrentes)
    assert avulsa["id"] not in {t["id"] for t in apenas_recorrentes}

    excluindo_recorrentes = auth_client.get(
        "/transacoes", params={"apenas_recorrentes": False}
    ).json()
    assert all(t["recorrencia_id"] is None for t in excluindo_recorrentes)
    assert avulsa["id"] in {t["id"] for t in excluindo_recorrentes}

    sem_filtro = auth_client.get("/transacoes").json()
    assert len(sem_filtro) == len(apenas_recorrentes) + len(excluindo_recorrentes)
