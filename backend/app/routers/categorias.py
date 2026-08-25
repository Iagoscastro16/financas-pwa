from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaRead, CategoriaUpdate

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def criar_categoria(payload: CategoriaCreate, db: Session = Depends(get_db)) -> Categoria:
    categoria = Categoria(**payload.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.get("", response_model=list[CategoriaRead])
def listar_categorias(
    include_inactive: bool = False, db: Session = Depends(get_db)
) -> list[Categoria]:
    stmt = select(Categoria)
    if not include_inactive:
        stmt = stmt.where(Categoria.ativo.is_(True))
    return list(db.execute(stmt).scalars().all())


@router.get("/{categoria_id}", response_model=CategoriaRead)
def obter_categoria(
    categoria_id: int, include_inactive: bool = False, db: Session = Depends(get_db)
) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None or (not categoria.ativo and not include_inactive):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    return categoria


@router.put("/{categoria_id}", response_model=CategoriaRead)
def atualizar_categoria(
    categoria_id: int, payload: CategoriaUpdate, db: Session = Depends(get_db)
) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_categoria(categoria_id: int, db: Session = Depends(get_db)) -> None:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    categoria.ativo = False
    db.commit()
