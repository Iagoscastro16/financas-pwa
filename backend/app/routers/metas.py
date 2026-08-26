from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import model_to_dict, registrar_auditoria
from app.auth import get_current_user
from app.database import get_db
from app.models.meta import Meta
from app.schemas.meta import MetaCreate, MetaRead, MetaUpdate

router = APIRouter(prefix="/metas", tags=["metas"], dependencies=[Depends(get_current_user)])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=MetaRead, status_code=status.HTTP_201_CREATED)
def criar_meta(
    payload: MetaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Meta:
    meta = Meta(**payload.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    registrar_auditoria(
        usuario=current_user,
        acao="create",
        entidade="meta",
        entidade_id=meta.id,
        detalhes={"novo": model_to_dict(meta)},
        ip_origem=_ip(request),
    )
    return meta


@router.get("", response_model=list[MetaRead])
def listar_metas(db: Session = Depends(get_db)) -> list[Meta]:
    return list(db.execute(select(Meta)).scalars().all())


@router.get("/{meta_id}", response_model=MetaRead)
def obter_meta(meta_id: int, db: Session = Depends(get_db)) -> Meta:
    meta = db.get(Meta, meta_id)
    if meta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meta não encontrada")
    return meta


@router.put("/{meta_id}", response_model=MetaRead)
def atualizar_meta(
    meta_id: int,
    payload: MetaUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Meta:
    meta = db.get(Meta, meta_id)
    if meta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meta não encontrada")
    antes = model_to_dict(meta)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(meta, campo, valor)
    db.commit()
    db.refresh(meta)
    registrar_auditoria(
        usuario=current_user,
        acao="update",
        entidade="meta",
        entidade_id=meta.id,
        detalhes={"antes": antes, "depois": model_to_dict(meta)},
        ip_origem=_ip(request),
    )
    return meta


@router.delete("/{meta_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_meta(
    meta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> None:
    meta = db.get(Meta, meta_id)
    if meta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meta não encontrada")
    antes = model_to_dict(meta)
    db.delete(meta)
    db.commit()
    registrar_auditoria(
        usuario=current_user,
        acao="delete",
        entidade="meta",
        entidade_id=meta_id,
        detalhes={"deletado": antes, "soft_delete": False},
        ip_origem=_ip(request),
    )
