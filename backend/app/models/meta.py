from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Meta(Base):
    __tablename__ = "meta"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    valor_alvo: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    valor_atual: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    prazo: Mapped[date | None] = mapped_column(Date, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
