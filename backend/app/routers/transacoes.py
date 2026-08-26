from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import model_to_dict, registrar_auditoria
from app.auth import get_current_user
from app.database import get_db
from app.models.categoria import Categoria
from app.models.conta import Conta
from app.models.transacao import Transacao
from app.schemas.transacao import TransacaoCreate, TransacaoRead, TransacaoUpdate

router = APIRouter(
    prefix="/transacoes", tags=["transacoes"], dependencies=[Depends(get_current_user)]
)


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _com_categoria_ids(transacao: Transacao) -> dict:
    return {**model_to_dict(transacao), "categoria_ids": [c.id for c in transacao.categorias]}


def _buscar_categorias(db: Session, categoria_ids: list[int]) -> list[Categoria]:
    if not categoria_ids:
        return []
    categorias = list(
        db.execute(select(Categoria).where(Categoria.id.in_(categoria_ids))).scalars().all()
    )
    encontrados = {c.id for c in categorias}
    faltando = set(categoria_ids) - encontrados
    if faltando:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categorias não encontradas: {sorted(faltando)}",
        )
    return categorias


@router.post("", response_model=TransacaoRead, status_code=status.HTTP_201_CREATED)
def criar_transacao(
    payload: TransacaoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Transacao:
    if db.get(Conta, payload.conta_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta não encontrada")

    dados = payload.model_dump(exclude={"categoria_ids"})
    transacao = Transacao(**dados)
    transacao.categorias = _buscar_categorias(db, payload.categoria_ids)
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    registrar_auditoria(
        usuario=current_user,
        acao="create",
        entidade="transacao",
        entidade_id=transacao.id,
        detalhes={"novo": _com_categoria_ids(transacao)},
        ip_origem=_ip(request),
    )
    return transacao


@router.get("", response_model=list[TransacaoRead])
def listar_transacoes(db: Session = Depends(get_db)) -> list[Transacao]:
    return list(db.execute(select(Transacao)).scalars().all())


@router.get("/{transacao_id}", response_model=TransacaoRead)
def obter_transacao(transacao_id: int, db: Session = Depends(get_db)) -> Transacao:
    transacao = db.get(Transacao, transacao_id)
    if transacao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")
    return transacao


@router.put("/{transacao_id}", response_model=TransacaoRead)
def atualizar_transacao(
    transacao_id: int,
    payload: TransacaoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Transacao:
    transacao = db.get(Transacao, transacao_id)
    if transacao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")

    antes = _com_categoria_ids(transacao)

    dados = payload.model_dump(exclude_unset=True, exclude={"categoria_ids"})
    if "conta_id" in dados and db.get(Conta, dados["conta_id"]) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta não encontrada")
    for campo, valor in dados.items():
        setattr(transacao, campo, valor)

    if payload.categoria_ids is not None:
        transacao.categorias = _buscar_categorias(db, payload.categoria_ids)

    db.commit()
    db.refresh(transacao)
    registrar_auditoria(
        usuario=current_user,
        acao="update",
        entidade="transacao",
        entidade_id=transacao.id,
        detalhes={"antes": antes, "depois": _com_categoria_ids(transacao)},
        ip_origem=_ip(request),
    )
    return transacao


@router.delete("/{transacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_transacao(
    transacao_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> None:
    transacao = db.get(Transacao, transacao_id)
    if transacao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")
    antes = _com_categoria_ids(transacao)
    db.delete(transacao)
    db.commit()
    registrar_auditoria(
        usuario=current_user,
        acao="delete",
        entidade="transacao",
        entidade_id=transacao_id,
        detalhes={"deletado": antes, "soft_delete": False},
        ip_origem=_ip(request),
    )
