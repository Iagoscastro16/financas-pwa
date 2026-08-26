import os

from passlib.context import CryptContext

TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword123"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Precisa ser definido ANTES de qualquer import de `app.*`, pois app.config lê
# essas variáveis de ambiente no momento da importação do módulo.
os.environ["AUTH_USERNAME"] = TEST_USERNAME
os.environ["AUTH_PASSWORD_HASH"] = _pwd_context.hash(TEST_PASSWORD)
os.environ["JWT_SECRET_KEY"] = "test-secret-key-used-only-in-pytest"
# Evita que o create_all(bind=engine) disparado na importação de app.main
# crie/toque no financas.db real: o app é montado sobre um banco em memória
# descartável, e cada teste usa seu próprio engine isolado via override de get_db.
os.environ["DATABASE_URL"] = "sqlite://"
# Mesma lógica para o log de auditoria: nunca tocar o auditoria.db real.
os.environ["AUDIT_DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.audit_database import AuditBase, AuditSessionLocal, audit_engine  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.limiter import limiter  # noqa: E402
from app.main import app  # noqa: E402
from app.models.log_auditoria import LogAuditoria  # noqa: E402

# audit_engine é um singleton de módulo (em memória, StaticPool) que vive por
# toda a sessão de testes — diferente do engine principal, que cada teste
# recria via a fixture `db_engine` abaixo. Antes, esse create_all acontecia
# como efeito colateral da importação de app.main; agora que main.py não cria
# mais schema em runtime (schema é responsabilidade do Alembic para bancos
# reais), os testes precisam criá-lo explicitamente aqui.
AuditBase.metadata.create_all(bind=audit_engine)


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Garante que os contadores do slowapi não vazem entre testes."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def _clear_audit_log():
    """O engine de auditoria é um singleton de módulo (em memória, StaticPool),
    então limpa a tabela antes/depois de cada teste para isolar os testes
    entre si."""

    def _limpar():
        db = AuditSessionLocal()
        try:
            db.query(LogAuditoria).delete()
            db.commit()
        finally:
            db.close()

    _limpar()
    yield
    _limpar()


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_engine):
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def auth_client(client):
    """Cliente já autenticado: faz login com as credenciais de teste e mantém
    o header Authorization configurado para as requisições seguintes."""
    response = client.post(
        "/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
