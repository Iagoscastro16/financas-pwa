from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import model_to_dict, registrar_auditoria
from app.auth import get_current_user
from app.database import get_db
from app.models.conta import Conta
from app.schemas.conta import ContaCreate, ContaRead, ContaUpdate

router = APIRouter(prefix="/contas", tags=["contas"], dependencies=[Depends(get_current_user)])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=ContaRead, status_code=status.HTTP_201_CREATED)
def criar_conta(
    payload: ContaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Conta:
    conta = Conta(**payload.model_dump())
    db.add(conta)
    db.commit()
    db.refresh(conta)
    registrar_auditoria(
        usuario=current_user,
        acao="create",
        entidade="conta",
        entidade_id=conta.id,
        detalhes={"novo": model_to_dict(conta)},
        ip_origem=_ip(request),
    )
    return conta


@router.get("", response_model=list[ContaRead])
def listar_contas(
    include_inactive: bool = False, db: Session = Depends(get_db)
) -> list[Conta]:
    stmt = select(Conta)
    if not include_inactive:
        stmt = stmt.where(Conta.ativo.is_(True))
    return list(db.execute(stmt).scalars().all())


@router.get("/{conta_id}", response_model=ContaRead)
def obter_conta(
    conta_id: int, include_inactive: bool = False, db: Session = Depends(get_db)
) -> Conta:
    conta = db.get(Conta, conta_id)
    if conta is None or (not conta.ativo and not include_inactive):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    return conta


@router.put("/{conta_id}", response_model=ContaRead)
def atualizar_conta(
    conta_id: int,
    payload: ContaUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Conta:
    conta = db.get(Conta, conta_id)
    if conta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    antes = model_to_dict(conta)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(conta, campo, valor)
    db.commit()
    db.refresh(conta)
    registrar_auditoria(
        usuario=current_user,
        acao="update",
        entidade="conta",
        entidade_id=conta.id,
        detalhes={"antes": antes, "depois": model_to_dict(conta)},
        ip_origem=_ip(request),
    )
    return conta


@router.delete("/{conta_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_conta(
    conta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> None:
    conta = db.get(Conta, conta_id)
    if conta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    antes = model_to_dict(conta)
    conta.ativo = False
    db.commit()
    registrar_auditoria(
        usuario=current_user,
        acao="delete",
        entidade="conta",
        entidade_id=conta_id,
        detalhes={"deletado": antes, "soft_delete": True},
        ip_origem=_ip(request),
    )
