from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import model_to_dict, registrar_auditoria
from app.auth import get_current_user
from app.database import get_db
from app.mes_ano import limites_mes
from app.models.categoria import Categoria
from app.models.conta import Conta
from app.models.transacao import Transacao
from app.models.transacao_categoria import TransacaoCategoria
from app.schemas.transacao import TransacaoCreate, TransacaoRead, TransacaoUpdate

router = APIRouter(
    prefix="/transacoes", tags=["transacoes"], dependencies=[Depends(get_current_user)]
)

ORDENACOES_VALIDAS = {"data_desc", "data_asc", "categoria"}


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
    if dados["data"] is None:
        dados["data"] = datetime.now()
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
def listar_transacoes(
    mes_ano: str | None = None,
    ordenar_por: str = "data_desc",
    db: Session = Depends(get_db),
) -> list[Transacao]:
    if ordenar_por not in ORDENACOES_VALIDAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ordenar_por deve ser um dos seguintes: {', '.join(sorted(ORDENACOES_VALIDAS))}",
        )

    stmt = select(Transacao)
    if mes_ano is not None:
        inicio, fim = limites_mes(mes_ano)
        stmt = stmt.where(Transacao.data >= inicio, Transacao.data < fim)

    if ordenar_por == "data_asc":
        stmt = stmt.order_by(Transacao.data.asc(), Transacao.id.asc())
    elif ordenar_por == "categoria":
        # Assunção: uma transação pode estar vinculada a várias categorias;
        # para ordenar por "a" categoria usamos a primeira delas. A tabela
        # de associação transacao_categoria só tem a chave composta
        # (transacao_id, categoria_id) — nenhuma coluna de ordem/insercao —
        # então a ordem real em que as categorias foram vinculadas não é
        # recuperável de forma portátil entre SQLite e Postgres. Como proxy
        # determinístico, usamos a categoria de menor id vinculada à
        # transação. Mesmo espírito de escolha pragmática da divisão
        # igualitária assumida em /resumo/categorias. Transações sem
        # nenhuma categoria não têm essa subconsulta preenchida (NULL) e
        # vão para o final da lista (nulls_last). Comparamos em minúsculas
        # porque "A-Z" para quem lê a lista é alfabetização
        # case-insensitive (ex.: "teste" antes de "Uber") — a ordenação
        # binária padrão do SQL colocaria toda maiúscula antes de qualquer
        # minúscula, o que não bate com a expectativa do usuário.
        primeira_categoria_nome = (
            select(func.lower(Categoria.nome))
            .select_from(TransacaoCategoria)
            .join(Categoria, Categoria.id == TransacaoCategoria.categoria_id)
            .where(TransacaoCategoria.transacao_id == Transacao.id)
            .order_by(TransacaoCategoria.categoria_id.asc())
            .limit(1)
            .scalar_subquery()
        )
        stmt = stmt.order_by(primeira_categoria_nome.asc().nulls_last(), Transacao.id.asc())
    else:
        stmt = stmt.order_by(Transacao.data.desc(), Transacao.id.desc())

    return list(db.execute(stmt).scalars().all())


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
