from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import model_to_dict, registrar_auditoria
from app.auth import get_current_user
from app.database import get_db
from app.models.categoria import Categoria
from app.models.conta import Conta
from app.models.transacao_recorrente import TransacaoRecorrente
from app.recorrencia import gerar_ocorrencia_se_devida
from app.schemas.transacao_recorrente import (
    TransacaoRecorrenteCreate,
    TransacaoRecorrenteRead,
    TransacaoRecorrenteUpdate,
)

router = APIRouter(
    prefix="/transacoes-recorrentes",
    tags=["transacoes-recorrentes"],
    dependencies=[Depends(get_current_user)],
)


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _com_categoria_ids(regra: TransacaoRecorrente) -> dict:
    return {**model_to_dict(regra), "categoria_ids": [c.id for c in regra.categorias]}


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


@router.post("", response_model=TransacaoRecorrenteRead, status_code=status.HTTP_201_CREATED)
def criar_transacao_recorrente(
    payload: TransacaoRecorrenteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> TransacaoRecorrente:
    if db.get(Conta, payload.conta_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta não encontrada")

    dados = payload.model_dump(exclude={"categoria_ids"})
    regra = TransacaoRecorrente(**dados)
    regra.categorias = _buscar_categorias(db, payload.categoria_ids)
    db.add(regra)
    db.commit()
    db.refresh(regra)

    registrar_auditoria(
        usuario=current_user,
        acao="create",
        entidade="transacao_recorrente",
        entidade_id=regra.id,
        detalhes={"novo": _com_categoria_ids(regra)},
        ip_origem=_ip(request),
    )

    # Backfill: se a ocorrência deste mês já estiver na data (ou no passado),
    # gera na hora em vez de esperar o próximo tick do scheduler.
    transacao_gerada = gerar_ocorrencia_se_devida(db, regra)
    if transacao_gerada is not None:
        registrar_auditoria(
            usuario=current_user,
            acao="create",
            entidade="transacao",
            entidade_id=transacao_gerada.id,
            detalhes={
                "novo": {
                    **model_to_dict(transacao_gerada),
                    "categoria_ids": [c.id for c in transacao_gerada.categorias],
                },
                "origem": "backfill_transacao_recorrente",
                "recorrencia_id": regra.id,
            },
            ip_origem=_ip(request),
        )
        db.refresh(regra)

    return regra


@router.get("", response_model=list[TransacaoRecorrenteRead])
def listar_transacoes_recorrentes(
    include_inactive: bool = False, db: Session = Depends(get_db)
) -> list[TransacaoRecorrente]:
    stmt = select(TransacaoRecorrente)
    if not include_inactive:
        stmt = stmt.where(TransacaoRecorrente.ativo.is_(True))
    return list(db.execute(stmt).scalars().all())


@router.get("/{recorrencia_id}", response_model=TransacaoRecorrenteRead)
def obter_transacao_recorrente(
    recorrencia_id: int, include_inactive: bool = False, db: Session = Depends(get_db)
) -> TransacaoRecorrente:
    regra = db.get(TransacaoRecorrente, recorrencia_id)
    if regra is None or (not regra.ativo and not include_inactive):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transação recorrente não encontrada"
        )
    return regra


@router.put("/{recorrencia_id}", response_model=TransacaoRecorrenteRead)
def atualizar_transacao_recorrente(
    recorrencia_id: int,
    payload: TransacaoRecorrenteUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> TransacaoRecorrente:
    regra = db.get(TransacaoRecorrente, recorrencia_id)
    if regra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transação recorrente não encontrada"
        )

    antes = _com_categoria_ids(regra)

    dados = payload.model_dump(exclude_unset=True, exclude={"categoria_ids"})
    for campo, valor in dados.items():
        setattr(regra, campo, valor)

    if payload.categoria_ids is not None:
        regra.categorias = _buscar_categorias(db, payload.categoria_ids)

    db.commit()
    db.refresh(regra)
    registrar_auditoria(
        usuario=current_user,
        acao="update",
        entidade="transacao_recorrente",
        entidade_id=regra.id,
        detalhes={"antes": antes, "depois": _com_categoria_ids(regra)},
        ip_origem=_ip(request),
    )
    return regra


@router.delete("/{recorrencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_transacao_recorrente(
    recorrencia_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> None:
    regra = db.get(TransacaoRecorrente, recorrencia_id)
    if regra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transação recorrente não encontrada"
        )
    antes = _com_categoria_ids(regra)
    regra.ativo = False
    db.commit()
    registrar_auditoria(
        usuario=current_user,
        acao="delete",
        entidade="transacao_recorrente",
        entidade_id=recorrencia_id,
        detalhes={"deletado": antes, "soft_delete": True},
        ip_origem=_ip(request),
    )
