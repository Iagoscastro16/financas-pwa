from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrcamentoBase(BaseModel):
    categoria_id: int
    mes_ano: str = Field(..., description='Formato "YYYY-MM"')
    valor_maximo: float = Field(..., gt=0)

    @field_validator("mes_ano")
    @classmethod
    def validar_mes_ano(cls, v: str) -> str:
        import re

        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", v):
            raise ValueError('mes_ano deve seguir o formato "YYYY-MM"')
        return v


class OrcamentoCreate(OrcamentoBase):
    pass


class OrcamentoUpdate(BaseModel):
    categoria_id: int | None = None
    mes_ano: str | None = None
    valor_maximo: float | None = Field(None, gt=0)


class OrcamentoRead(OrcamentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
