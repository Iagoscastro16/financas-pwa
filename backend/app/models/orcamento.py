from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Orcamento(Base):
    __tablename__ = "orcamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), nullable=False)
    mes_ano: Mapped[str] = mapped_column(String(7), nullable=False)  # formato "YYYY-MM"
    valor_maximo: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    categoria: Mapped["Categoria"] = relationship(back_populates="orcamentos")
