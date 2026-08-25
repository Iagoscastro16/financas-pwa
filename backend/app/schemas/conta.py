from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContaBase(BaseModel):
    nome: str = Field(..., max_length=100)
    saldo_inicial: float = 0


class ContaCreate(ContaBase):
    pass


class ContaUpdate(BaseModel):
    nome: str | None = Field(None, max_length=100)
    saldo_inicial: float | None = None


class ContaRead(ContaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    criado_em: datetime
