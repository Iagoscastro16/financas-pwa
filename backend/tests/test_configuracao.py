import json


def test_obter_configuracao_nao_definida_retorna_default(auth_client):
    response = auth_client.get("/configuracao/total_categoria_separado")
    assert response.status_code == 200
    body = response.json()
    assert body["chave"] == "total_categoria_separado"
    assert body["valor"] is False
    assert body["atualizado_em"] is None


def test_obter_configuracao_chave_desconhecida_404(auth_client):
    response = auth_client.get("/configuracao/chave_que_nao_existe")
    assert response.status_code == 404


def test_put_depois_get_reflete_novo_valor(auth_client):
    put_response = auth_client.put(
        "/configuracao/total_categoria_separado", json={"valor": True}
    )
    assert put_response.status_code == 200
    body = put_response.json()
    assert body["valor"] is True
    assert body["atualizado_em"] is not None

    get_response = auth_client.get("/configuracao/total_categoria_separado")
    assert get_response.status_code == 200
    assert get_response.json()["valor"] is True


def test_put_atualiza_valor_existente(auth_client):
    auth_client.put("/configuracao/total_categoria_separado", json={"valor": True})
    segunda = auth_client.put("/configuracao/total_categoria_separado", json={"valor": False})
    assert segunda.status_code == 200
    assert segunda.json()["valor"] is False


def test_listar_configuracoes(auth_client):
    auth_client.put("/configuracao/total_categoria_separado", json={"valor": True})

    response = auth_client.get("/configuracao")
    assert response.status_code == 200
    chaves = {c["chave"] for c in response.json()}
    assert "total_categoria_separado" in chaves


def test_obter_configuracao_percentual_nao_definida_retorna_default_string(auth_client):
    response = auth_client.get("/configuracao/orcamento_limite_alerta_percentual")
    assert response.status_code == 200
    body = response.json()
    assert body["chave"] == "orcamento_limite_alerta_percentual"
    assert body["valor"] == "80"
    assert isinstance(body["valor"], str)
    assert body["atualizado_em"] is None


def test_put_percentual_valido_persiste_como_string(auth_client):
    put_response = auth_client.put(
        "/configuracao/orcamento_limite_alerta_percentual", json={"valor": "65"}
    )
    assert put_response.status_code == 200
    body = put_response.json()
    assert body["valor"] == "65"
    assert isinstance(body["valor"], str)

    get_response = auth_client.get("/configuracao/orcamento_limite_alerta_percentual")
    assert get_response.json()["valor"] == "65"


def test_put_percentual_nao_numerico_e_rejeitado(auth_client):
    response = auth_client.put(
        "/configuracao/orcamento_limite_alerta_percentual", json={"valor": "abacate"}
    )
    assert response.status_code == 422


def test_put_percentual_fora_da_faixa_e_rejeitado(auth_client):
    acima = auth_client.put(
        "/configuracao/orcamento_limite_alerta_percentual", json={"valor": "101"}
    )
    assert acima.status_code == 422

    abaixo = auth_client.put(
        "/configuracao/orcamento_limite_alerta_percentual", json={"valor": "0"}
    )
    assert abaixo.status_code == 422


def test_put_percentual_nos_limites_da_faixa_e_aceito(auth_client):
    minimo = auth_client.put(
        "/configuracao/orcamento_limite_alerta_percentual", json={"valor": "1"}
    )
    assert minimo.status_code == 200

    maximo = auth_client.put(
        "/configuracao/orcamento_limite_alerta_percentual", json={"valor": "100"}
    )
    assert maximo.status_code == 200


def test_put_total_categoria_separado_com_string_e_rejeitado(auth_client):
    """Chave booleana conhecida deve continuar exigindo bool na API, não
    aceitando uma string mesmo que pareça um booleano."""
    response = auth_client.put(
        "/configuracao/total_categoria_separado", json={"valor": "true"}
    )
    assert response.status_code == 422


def test_put_e_registrado_na_auditoria(auth_client):
    auth_client.put("/configuracao/total_categoria_separado", json={"valor": True})

    log_response = auth_client.get(
        "/auditoria", params={"entidade": "configuracao", "acao": "update"}
    )
    assert log_response.status_code == 200
    logs = log_response.json()
    assert logs, "esperava pelo menos um log de auditoria para configuracao"

    log = logs[0]
    assert log["entidade_id"] is None
    detalhes = json.loads(log["detalhes"])
    assert detalhes["chave"] == "total_categoria_separado"
    assert detalhes["valor_antigo"] is False
    assert detalhes["valor_novo"] is True
