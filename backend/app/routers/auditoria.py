from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit_database import get_audit_db
from app.auth import get_current_user
from app.models.log_auditoria import LogAuditoria
from app.schemas.auditoria import LogAuditoriaRead

router = APIRouter(
    prefix="/auditoria", tags=["auditoria"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[LogAuditoriaRead])
def listar_auditoria(
    entidade: str | None = None,
    acao: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_audit_db),
) -> list[LogAuditoria]:
    stmt = select(LogAuditoria).order_by(LogAuditoria.id.desc())
    if entidade is not None:
        stmt = stmt.where(LogAuditoria.entidade == entidade)
    if acao is not None:
        stmt = stmt.where(LogAuditoria.acao == acao)
    stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())
