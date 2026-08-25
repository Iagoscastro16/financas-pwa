from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransacaoCategoria(Base):
    __tablename__ = "transacao_categoria"

    transacao_id: Mapped[int] = mapped_column(ForeignKey("transacao.id"), primary_key=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), primary_key=True)
