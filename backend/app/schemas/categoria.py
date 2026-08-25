from pydantic import BaseModel, ConfigDict, Field

from app.models.categoria import TipoCategoria


class CategoriaBase(BaseModel):
    nome: str = Field(..., max_length=100)
    tipo: TipoCategoria


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nome: str | None = Field(None, max_length=100)
    tipo: TipoCategoria | None = None


class CategoriaRead(CategoriaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
