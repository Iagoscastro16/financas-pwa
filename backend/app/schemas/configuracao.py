from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConfiguracaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chave: str
    # bool para chaves booleanas conhecidas (ex.: total_categoria_separado,
    # preservando o contrato existente da API); str para qualquer outra
    # chave (números incluídos, ex.: "80") — ver CHAVES_BOOLEANAS no router.
    valor: bool | str
    # None quando a chave nunca foi definida e o valor devolvido é o default
    # hardcoded (não existe linha correspondente no banco).
    atualizado_em: datetime | None = None


class ConfiguracaoUpdate(BaseModel):
    valor: bool | str
