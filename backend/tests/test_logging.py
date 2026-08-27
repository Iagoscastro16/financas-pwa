import logging

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


def test_excecao_nao_tratada_e_logada_e_retorna_500_generico(auth_client, caplog):
    """Uma exceção não tratada dentro de uma rota deve: (1) ser registrada no
    log técnico com traceback completo, e (2) resultar numa resposta 500
    genérica ao cliente, sem vazar detalhes internos (mensagem da exceção,
    nome da classe, traceback) no corpo da resposta HTTP.

    Usa um TestClient local com raise_server_exceptions=False: por padrão o
    Starlette TestClient relança a exceção mesmo depois do handler de 500 já
    ter montado a resposta (é assim que ele sinaliza "isto não foi tratado"
    para quem está testando) — o que impediria justamente de inspecionar a
    resposta 500 genérica que o handler devolve ao cliente real.
    """

    def get_db_quebrado():
        raise RuntimeError("falha proposital para teste de logging")

    app.dependency_overrides[get_db] = get_db_quebrado

    with TestClient(app, raise_server_exceptions=False) as cliente:
        cliente.headers.update(auth_client.headers)
        with caplog.at_level(logging.ERROR, logger="app.main"):
            response = cliente.get("/contas")

    assert response.status_code == 500
    assert response.json() == {"detail": "Erro interno do servidor"}
    assert "falha proposital" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text

    mensagens = [registro.getMessage() for registro in caplog.records]
    assert any("Erro não tratado" in mensagem for mensagem in mensagens)
    # logger.exception (não logger.error) deve ter anexado o traceback
    assert any(registro.exc_info is not None for registro in caplog.records)


def test_falha_ao_registrar_auditoria_e_logada_em_vez_de_impressa(auth_client, monkeypatch, caplog):
    """registrar_auditoria não deve mais usar print(): uma falha ao gravar em
    auditoria.db deve aparecer no log técnico (com traceback) e, mesmo assim,
    a operação principal deve concluir normalmente."""
    import app.audit as audit_module

    def _quebra(*args, **kwargs):
        raise RuntimeError("falha simulada de auditoria")

    monkeypatch.setattr(audit_module, "AuditSessionLocal", _quebra)

    with caplog.at_level(logging.ERROR, logger="app.audit"):
        response = auth_client.post("/contas", json={"nome": "Sobrevive ao log"})

    assert response.status_code == 201
    assert response.json()["nome"] == "Sobrevive ao log"

    mensagens = [registro.getMessage() for registro in caplog.records]
    assert any("Falha ao registrar log de auditoria" in mensagem for mensagem in mensagens)
    assert any(registro.exc_info is not None for registro in caplog.records)
