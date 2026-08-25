from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.transacao import TipoTransacao
from app.schemas.categoria import CategoriaRead


class TransacaoBase(BaseModel):
    conta_id: int
    tipo: TipoTransacao
    valor: float = Field(..., gt=0)
    data: date
    descricao: str | None = Field(None, max_length=255)


class TransacaoCreate(TransacaoBase):
    categoria_ids: list[int] = Field(default_factory=list)


class TransacaoUpdate(BaseModel):
    conta_id: int | None = None
    tipo: TipoTransacao | None = None
    valor: float | None = Field(None, gt=0)
    data: date | None = None
    descricao: str | None = Field(None, max_length=255)
    categoria_ids: list[int] | None = None


class TransacaoRead(TransacaoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
    categorias: list[CategoriaRead] = Field(default_factory=list)
