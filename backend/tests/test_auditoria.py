import json

from app.audit import registrar_auditoria


def _ultimo_log(auth_client, **filtros):
    response = auth_client.get("/auditoria", params=filtros)
    assert response.status_code == 200
    entradas = response.json()
    assert entradas, "esperava pelo menos uma entrada de auditoria"
    return entradas[0]


def test_criar_conta_gera_log_de_auditoria(auth_client):
    conta = auth_client.post("/contas", json={"nome": "Carteira"}).json()

    log = _ultimo_log(auth_client, entidade="conta", acao="create")
    assert log["acao"] == "create"
    assert log["entidade"] == "conta"
    assert log["entidade_id"] == conta["id"]
    detalhes = json.loads(log["detalhes"])
    assert detalhes["novo"]["nome"] == "Carteira"


def test_atualizar_conta_gera_log_com_antes_e_depois(auth_client):
    conta = auth_client.post("/contas", json={"nome": "Original"}).json()
    auth_client.put(f"/contas/{conta['id']}", json={"nome": "Atualizada"})

    log = _ultimo_log(auth_client, entidade="conta", acao="update")
    assert log["entidade_id"] == conta["id"]
    detalhes = json.loads(log["detalhes"])
    assert detalhes["antes"]["nome"] == "Original"
    assert detalhes["depois"]["nome"] == "Atualizada"


def test_remover_conta_gera_log_de_soft_delete(auth_client):
    conta = auth_client.post("/contas", json={"nome": "Para remover"}).json()
    auth_client.delete(f"/contas/{conta['id']}")

    log = _ultimo_log(auth_client, entidade="conta", acao="delete")
    assert log["entidade_id"] == conta["id"]
    detalhes = json.loads(log["detalhes"])
    assert detalhes["soft_delete"] is True
    assert detalhes["deletado"]["nome"] == "Para remover"


def test_remover_meta_gera_log_de_hard_delete(auth_client):
    meta = auth_client.post("/metas", json={"nome": "Meta", "valor_alvo": 100}).json()
    auth_client.delete(f"/metas/{meta['id']}")

    log = _ultimo_log(auth_client, entidade="meta", acao="delete")
    assert log["entidade_id"] == meta["id"]
    detalhes = json.loads(log["detalhes"])
    assert detalhes["soft_delete"] is False


def test_login_bem_sucedido_gera_log(auth_client):
    log = _ultimo_log(auth_client, entidade="auth", acao="login")
    assert log["usuario"] == "testuser"
    detalhes = json.loads(log["detalhes"])
    assert "senha" not in json.dumps(detalhes).lower()
    assert "password" not in json.dumps(detalhes).lower()


def test_login_falho_nao_vaza_senha(client):
    senha_secreta = "SenhaSecretaNuncaDeveVazar123"
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": senha_secreta}
    )
    assert response.status_code == 401

    # faz login de verdade só para poder consultar o endpoint de auditoria
    login_valido = client.post(
        "/auth/login", json={"username": "testuser", "password": "testpassword123"}
    )
    token = login_valido.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    response = client.get("/auditoria", params={"entidade": "auth", "acao": "login_failed"})
    assert response.status_code == 200
    entradas = response.json()
    assert entradas

    corpo_completo = json.dumps(entradas)
    assert senha_secreta not in corpo_completo

    falha = entradas[0]
    assert falha["usuario"] == "testuser"
    detalhes = json.loads(falha["detalhes"])
    assert senha_secreta not in json.dumps(detalhes)
    assert detalhes["motivo"] == "credenciais inválidas"


def test_detalhes_grandes_sao_truncados_sem_falhar(auth_client):
    detalhes_enormes = {"campo_gigante": "x" * 10_000}

    # Chamada direta ao helper (não deve levantar exceção nem falhar a operação).
    registrar_auditoria(
        usuario="testuser",
        acao="update",
        entidade="conta",
        entidade_id=1,
        detalhes=detalhes_enormes,
    )

    log = _ultimo_log(auth_client, entidade="conta", acao="update")
    assert len(log["detalhes"]) <= 2000
    detalhes = json.loads(log["detalhes"])
    assert detalhes["_truncated"] is True


def test_operacao_principal_sobrevive_a_falha_de_auditoria(auth_client, monkeypatch):
    import app.audit as audit_module

    def _quebra(*args, **kwargs):
        raise RuntimeError("falha simulada de auditoria")

    monkeypatch.setattr(audit_module, "AuditSessionLocal", _quebra)

    response = auth_client.post("/contas", json={"nome": "Sobrevive"})
    assert response.status_code == 201
    assert response.json()["nome"] == "Sobrevive"
