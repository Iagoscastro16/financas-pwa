from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConfiguracaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chave: str
    valor: bool
    # None quando a chave nunca foi definida e o valor devolvido é o default
    # hardcoded (não existe linha correspondente no banco).
    atualizado_em: datetime | None = None


class ConfiguracaoUpdate(BaseModel):
    valor: bool
