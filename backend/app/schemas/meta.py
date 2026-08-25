from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MetaBase(BaseModel):
    nome: str = Field(..., max_length=100)
    valor_alvo: float = Field(..., gt=0)
    valor_atual: float = 0
    prazo: date | None = None


class MetaCreate(MetaBase):
    pass


class MetaUpdate(BaseModel):
    nome: str | None = Field(None, max_length=100)
    valor_alvo: float | None = Field(None, gt=0)
    valor_atual: float | None = None
    prazo: date | None = None


class MetaRead(MetaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
