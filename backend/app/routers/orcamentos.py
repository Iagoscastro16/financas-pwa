from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.categoria import Categoria
from app.models.orcamento import Orcamento
from app.schemas.orcamento import OrcamentoCreate, OrcamentoRead, OrcamentoUpdate

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])


@router.post("", response_model=OrcamentoRead, status_code=status.HTTP_201_CREATED)
def criar_orcamento(payload: OrcamentoCreate, db: Session = Depends(get_db)) -> Orcamento:
    if db.get(Categoria, payload.categoria_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria não encontrada")
    orcamento = Orcamento(**payload.model_dump())
    db.add(orcamento)
    db.commit()
    db.refresh(orcamento)
    return orcamento


@router.get("", response_model=list[OrcamentoRead])
def listar_orcamentos(db: Session = Depends(get_db)) -> list[Orcamento]:
    return list(db.execute(select(Orcamento)).scalars().all())


@router.get("/{orcamento_id}", response_model=OrcamentoRead)
def obter_orcamento(orcamento_id: int, db: Session = Depends(get_db)) -> Orcamento:
    orcamento = db.get(Orcamento, orcamento_id)
    if orcamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")
    return orcamento


@router.put("/{orcamento_id}", response_model=OrcamentoRead)
def atualizar_orcamento(
    orcamento_id: int, payload: OrcamentoUpdate, db: Session = Depends(get_db)
) -> Orcamento:
    orcamento = db.get(Orcamento, orcamento_id)
    if orcamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")

    dados = payload.model_dump(exclude_unset=True)
    if "categoria_id" in dados and db.get(Categoria, dados["categoria_id"]) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria não encontrada")
    for campo, valor in dados.items():
        setattr(orcamento, campo, valor)
    db.commit()
    db.refresh(orcamento)
    return orcamento


@router.delete("/{orcamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_orcamento(orcamento_id: int, db: Session = Depends(get_db)) -> None:
    orcamento = db.get(Orcamento, orcamento_id)
    if orcamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")
    db.delete(orcamento)
    db.commit()
