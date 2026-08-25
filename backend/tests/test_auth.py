from datetime import UTC, datetime, timedelta

from jose import jwt

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from tests.conftest import TEST_PASSWORD, TEST_USERNAME


def test_login_com_credenciais_corretas(client):
    response = client.post(
        "/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]

    payload = jwt.decode(body["access_token"], JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == TEST_USERNAME


def test_login_senha_incorreta(client):
    response = client.post(
        "/auth/login", json={"username": TEST_USERNAME, "password": "senha-errada"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Usuário ou senha inválidos"}


def test_login_usuario_incorreto(client):
    response = client.post(
        "/auth/login", json={"username": "outro-usuario", "password": TEST_PASSWORD}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Usuário ou senha inválidos"}


def test_login_mensagem_nao_revela_qual_campo_esta_errado(client):
    resposta_senha_errada = client.post(
        "/auth/login", json={"username": TEST_USERNAME, "password": "senha-errada"}
    )
    resposta_usuario_errado = client.post(
        "/auth/login", json={"username": "outro-usuario", "password": TEST_PASSWORD}
    )
    assert resposta_senha_errada.status_code == resposta_usuario_errado.status_code == 401
    assert resposta_senha_errada.json() == resposta_usuario_errado.json()


def test_rota_protegida_sem_token(client):
    response = client.get("/contas")
    assert response.status_code == 401


def test_rota_protegida_com_token_malformado(client):
    response = client.get("/contas", headers={"Authorization": "Bearer nao.e.um.jwt.valido"})
    assert response.status_code == 401


def test_rota_protegida_com_token_expirado(client):
    payload_expirado = {
        "sub": TEST_USERNAME,
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    token_expirado = jwt.encode(payload_expirado, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    response = client.get(
        "/contas", headers={"Authorization": f"Bearer {token_expirado}"}
    )
    assert response.status_code == 401


def test_rota_protegida_com_token_valido(auth_client):
    response = auth_client.get("/contas")
    assert response.status_code == 200


def test_rate_limit_apos_tentativas_repetidas(client):
    respostas = [
        client.post(
            "/auth/login", json={"username": TEST_USERNAME, "password": "senha-errada"}
        )
        for _ in range(6)
    ]

    codigos = [r.status_code for r in respostas]
    assert 401 in codigos
    assert 429 in codigos
    # a partir do momento em que o limite é excedido, todas as respostas seguintes
    # devem ser bloqueadas
    primeiro_429 = codigos.index(429)
    assert all(codigo == 429 for codigo in codigos[primeiro_429:])
