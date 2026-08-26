from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import model_to_dict, registrar_auditoria
from app.auth import get_current_user
from app.database import get_db
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaRead, CategoriaUpdate

router = APIRouter(
    prefix="/categorias", tags=["categorias"], dependencies=[Depends(get_current_user)]
)


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def criar_categoria(
    payload: CategoriaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Categoria:
    categoria = Categoria(**payload.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    registrar_auditoria(
        usuario=current_user,
        acao="create",
        entidade="categoria",
        entidade_id=categoria.id,
        detalhes={"novo": model_to_dict(categoria)},
        ip_origem=_ip(request),
    )
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
    categoria_id: int,
    payload: CategoriaUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    antes = model_to_dict(categoria)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)
    db.commit()
    db.refresh(categoria)
    registrar_auditoria(
        usuario=current_user,
        acao="update",
        entidade="categoria",
        entidade_id=categoria.id,
        detalhes={"antes": antes, "depois": model_to_dict(categoria)},
        ip_origem=_ip(request),
    )
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_categoria(
    categoria_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> None:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
    antes = model_to_dict(categoria)
    categoria.ativo = False
    db.commit()
    registrar_auditoria(
        usuario=current_user,
        acao="delete",
        entidade="categoria",
        entidade_id=categoria_id,
        detalhes={"deletado": antes, "soft_delete": True},
        ip_origem=_ip(request),
    )
