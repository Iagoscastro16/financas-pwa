import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

AUDIT_DATABASE_URL = os.environ.get("AUDIT_DATABASE_URL", "sqlite:///./auditoria.db")

_engine_kwargs: dict = {"connect_args": {"check_same_thread": False}}
if AUDIT_DATABASE_URL == "sqlite://":
    # Banco em memória (usado em testes): precisa de StaticPool para que a
    # mesma base seja compartilhada entre conexões/threads diferentes.
    _engine_kwargs["poolclass"] = StaticPool

audit_engine = create_engine(AUDIT_DATABASE_URL, **_engine_kwargs)

AuditSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=audit_engine)


class AuditBase(DeclarativeBase):
    """Base declarativa isolada do `Base` principal (app/database.py).

    Mantém o log de auditoria em um engine/arquivo (auditoria.db) totalmente
    separado do banco de dados principal (financas.db), servindo de base
    para futuramente migrar para uma instância Postgres dedicada.
    """


def get_audit_db() -> Generator[Session, None, None]:
    db = AuditSessionLocal()
    try:
        yield db
    finally:
        db.close()
