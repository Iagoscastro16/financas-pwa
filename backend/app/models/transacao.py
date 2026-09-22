import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoTransacao(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"


class Transacao(Base):
    __tablename__ = "transacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    conta_id: Mapped[int] = mapped_column(ForeignKey("conta.id"), nullable=False)
    tipo: Mapped[TipoTransacao] = mapped_column(SAEnum(TipoTransacao), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    data: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Vínculo apenas informativo com a regra que gerou esta transação: ON
    # DELETE SET NULL garante que, se a regra for excluída de fato do banco,
    # as transações já geradas continuam existindo normalmente como
    # transações avulsas, só perdendo a referência.
    recorrencia_id: Mapped[int | None] = mapped_column(
        ForeignKey("transacao_recorrente.id", ondelete="SET NULL"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conta: Mapped["Conta"] = relationship(back_populates="transacoes")
    categorias: Mapped[list["Categoria"]] = relationship(
        secondary="transacao_categoria", back_populates="transacoes"
    )
    recorrencia: Mapped["TransacaoRecorrente | None"] = relationship(
        back_populates="transacoes_geradas"
    )
