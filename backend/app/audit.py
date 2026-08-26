import json
import sys
from typing import Any

from app.audit_database import AuditSessionLocal
from app.models.log_auditoria import LogAuditoria

DETALHES_MAX_LENGTH = 2000


def model_to_dict(obj: Any) -> dict:
    """Converte uma instância de model SQLAlchemy num dict de colunas simples,
    pronto para ser serializado em JSON (via `json.dumps(..., default=str)`)."""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _serializar_detalhes(detalhes: dict | None) -> str | None:
    if detalhes is None:
        return None

    serializado = json.dumps(detalhes, default=str, ensure_ascii=False)
    if len(serializado) <= DETALHES_MAX_LENGTH:
        return serializado

    # Excede o limite: envelopa uma versão truncada do JSON original,
    # marcando explicitamente que houve truncamento, em vez de falhar a
    # requisição ou gravar um blob sem limite de tamanho.
    raw = serializado
    tamanho_raw = DETALHES_MAX_LENGTH
    for _ in range(10):
        candidato = json.dumps({"_truncated": True, "_raw": raw[:tamanho_raw]}, ensure_ascii=False)
        excesso = len(candidato) - DETALHES_MAX_LENGTH
        if excesso <= 0:
            return candidato
        tamanho_raw = max(tamanho_raw - excesso, 0)

    return candidato[:DETALHES_MAX_LENGTH]


def registrar_auditoria(
    *,
    usuario: str,
    acao: str,
    entidade: str,
    entidade_id: int | None = None,
    detalhes: dict | None = None,
    ip_origem: str | None = None,
) -> None:
    """Grava uma entrada de log de auditoria (append-only).

    Falhas ao registrar o log NUNCA devem interromper a operação principal
    (create/update/delete/login): qualquer exceção aqui é capturada e
    reportada apenas em stderr.
    """
    try:
        detalhes_serializados = _serializar_detalhes(detalhes)
        db = AuditSessionLocal()
        try:
            log = LogAuditoria(
                usuario=usuario,
                acao=acao,
                entidade=entidade,
                entidade_id=entidade_id,
                detalhes=detalhes_serializados,
                ip_origem=ip_origem,
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001 — logging nunca pode derrubar a operação principal
        print(f"[auditoria] falha ao registrar log de auditoria: {exc}", file=sys.stderr)
