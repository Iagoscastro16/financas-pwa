from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LogAuditoriaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    usuario: str
    acao: str
    entidade: str
    entidade_id: int | None
    detalhes: str | None
    ip_origem: str | None
