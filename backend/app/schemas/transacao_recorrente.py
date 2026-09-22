from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.transacao import TipoTransacao
from app.schemas.categoria import CategoriaRead


class TransacaoRecorrenteBase(BaseModel):
    nome: str = Field(..., max_length=255)
    valor: float = Field(..., gt=0)
    tipo: TipoTransacao
    conta_id: int
    dia_mes: int = Field(..., ge=1, le=31)
    data_inicio: date
    data_fim: date | None = None


class TransacaoRecorrenteCreate(TransacaoRecorrenteBase):
    categoria_ids: list[int] = Field(default_factory=list)


class TransacaoRecorrenteUpdate(BaseModel):
    # Só os campos que controlam o comportamento futuro da regra podem ser
    # editados (tipo, conta_id e data_inicio definem a regra em si e não são
    # alteráveis depois de criada). Editar nunca retroage sobre transações já
    # geradas.
    nome: str | None = Field(None, max_length=255)
    valor: float | None = Field(None, gt=0)
    dia_mes: int | None = Field(None, ge=1, le=31)
    data_fim: date | None = None
    categoria_ids: list[int] | None = None


class TransacaoRecorrenteRead(TransacaoRecorrenteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    ultima_geracao: date | None
    criado_em: datetime
    categorias: list[CategoriaRead] = Field(default_factory=list)
