from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import model_to_dict, registrar_auditoria
from app.auth import get_current_user
from app.database import get_db
from app.models.categoria import Categoria
from app.models.orcamento import Orcamento
from app.schemas.orcamento import OrcamentoCreate, OrcamentoRead, OrcamentoUpdate

router = APIRouter(
    prefix="/orcamentos", tags=["orcamentos"], dependencies=[Depends(get_current_user)]
)


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=OrcamentoRead, status_code=status.HTTP_201_CREATED)
def criar_orcamento(
    payload: OrcamentoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Orcamento:
    if db.get(Categoria, payload.categoria_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria não encontrada")
    orcamento = Orcamento(**payload.model_dump())
    db.add(orcamento)
    db.commit()
    db.refresh(orcamento)
    registrar_auditoria(
        usuario=current_user,
        acao="create",
        entidade="orcamento",
        entidade_id=orcamento.id,
        detalhes={"novo": model_to_dict(orcamento)},
        ip_origem=_ip(request),
    )
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
    orcamento_id: int,
    payload: OrcamentoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Orcamento:
    orcamento = db.get(Orcamento, orcamento_id)
    if orcamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")

    antes = model_to_dict(orcamento)
    dados = payload.model_dump(exclude_unset=True)
    if "categoria_id" in dados and db.get(Categoria, dados["categoria_id"]) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria não encontrada")
    for campo, valor in dados.items():
        setattr(orcamento, campo, valor)
    db.commit()
    db.refresh(orcamento)
    registrar_auditoria(
        usuario=current_user,
        acao="update",
        entidade="orcamento",
        entidade_id=orcamento.id,
        detalhes={"antes": antes, "depois": model_to_dict(orcamento)},
        ip_origem=_ip(request),
    )
    return orcamento


@router.delete("/{orcamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_orcamento(
    orcamento_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> None:
    orcamento = db.get(Orcamento, orcamento_id)
    if orcamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")
    antes = model_to_dict(orcamento)
    db.delete(orcamento)
    db.commit()
    registrar_auditoria(
        usuario=current_user,
        acao="delete",
        entidade="orcamento",
        entidade_id=orcamento_id,
        detalhes={"deletado": antes, "soft_delete": False},
        ip_origem=_ip(request),
    )
