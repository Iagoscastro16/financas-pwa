from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.transacao import TipoTransacao


class TransacaoRecorrente(Base):
    __tablename__ = "transacao_recorrente"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tipo: Mapped[TipoTransacao] = mapped_column(SAEnum(TipoTransacao), nullable=False)
    conta_id: Mapped[int] = mapped_column(ForeignKey("conta.id"), nullable=False)
    dia_mes: Mapped[int] = mapped_column(Integer, nullable=False)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Data da ocorrência mais recentemente gerada por esta regra — permite ao
    # job do scheduler checar "já gerei o mês corrente?" com uma leitura na
    # própria regra, sem varrer a tabela `transacao` por regra a cada execução.
    ultima_geracao: Mapped[date | None] = mapped_column(Date, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conta: Mapped["Conta"] = relationship()
    categorias: Mapped[list["Categoria"]] = relationship(
        secondary="transacao_recorrente_categoria"
    )
    transacoes_geradas: Mapped[list["Transacao"]] = relationship(
        back_populates="recorrencia"
    )
