import enum

from sqlalchemy import Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoCategoria(str, enum.Enum):
    receita = "receita"
    despesa = "despesa"


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoCategoria] = mapped_column(SAEnum(TipoCategoria), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    transacoes: Mapped[list["Transacao"]] = relationship(
        secondary="transacao_categoria", back_populates="categorias"
    )
    orcamentos: Mapped[list["Orcamento"]] = relationship(
        back_populates="categoria", cascade="all, delete-orphan"
    )
