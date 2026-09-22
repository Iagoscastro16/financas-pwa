from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransacaoRecorrenteCategoria(Base):
    __tablename__ = "transacao_recorrente_categoria"

    transacao_recorrente_id: Mapped[int] = mapped_column(
        ForeignKey("transacao_recorrente.id"), primary_key=True
    )
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), primary_key=True)
