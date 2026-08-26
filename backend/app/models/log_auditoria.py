from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.audit_database import AuditBase


class LogAuditoria(AuditBase):
    """Entrada de log de auditoria — somente inserção.

    Não deve existir, em nenhum lugar do código, nenhum método de
    update/delete para este modelo: o log de auditoria é append-only
    por design.
    """

    __tablename__ = "log_auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    usuario: Mapped[str] = mapped_column(String(100), nullable=False)
    acao: Mapped[str] = mapped_column(String(20), nullable=False)
    entidade: Mapped[str] = mapped_column(String(20), nullable=False)
    entidade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detalhes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_origem: Mapped[str | None] = mapped_column(String(45), nullable=True)
