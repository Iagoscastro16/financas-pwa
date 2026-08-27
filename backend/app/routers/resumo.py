from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.mes_ano import limites_mes
from app.models.conta import Conta
from app.models.transacao import Transacao, TipoTransacao
from app.routers.configuracao import obter_valor_config
from app.schemas.resumo import ResumoCategoria, ResumoComparativo, ResumoMensal, VariacaoPercentual

router = APIRouter(prefix="/resumo", tags=["resumo"], dependencies=[Depends(get_current_user)])

SEM_CATEGORIA_NOME = "Sem categoria"


def _mes_atual() -> str:
    return date.today().strftime("%Y-%m")


def _saldo_total_contas(db: Session) -> float:
    """Saldo atual real: saldo_inicial + todas as transações (de sempre,
    sem filtro de mês) de cada conta ATIVA."""
    contas_ativas = list(db.execute(select(Conta).where(Conta.ativo.is_(True))).scalars().all())
    saldo_inicial_total = sum(float(c.saldo_inicial) for c in contas_ativas)

    conta_ids = [c.id for c in contas_ativas]
    if not conta_ids:
        return saldo_inicial_total

    linhas = db.execute(
        select(Transacao.tipo, Transacao.valor).where(Transacao.conta_id.in_(conta_ids))
    ).all()
    dados = [(tipo.value, float(valor)) for tipo, valor in linhas]
    df = pd.DataFrame(dados, columns=["tipo", "valor"])
    if df.empty:
        return saldo_inicial_total

    sinal = df["tipo"].map(lambda t: 1 if t == TipoTransacao.entrada.value else -1)
    movimentacao = float((df["valor"] * sinal).sum())
    return saldo_inicial_total + movimentacao


def _resumo_mensal(db: Session, mes_ano: str) -> ResumoMensal:
    inicio, fim = limites_mes(mes_ano)
    linhas = db.execute(
        select(Transacao.tipo, Transacao.valor).where(Transacao.data >= inicio, Transacao.data < fim)
    ).all()
    # Converte o enum para seu `.value` (string simples) antes de criar o
    # DataFrame: pandas >= 3 infere um dtype "str" para colunas-objeto e
    # acaba usando repr(enum) internamente, o que quebra comparações `==`
    # contra o próprio membro do enum (mas não `.map`, por isso o cuidado).
    dados = [(tipo.value, float(valor)) for tipo, valor in linhas]
    df = pd.DataFrame(dados, columns=["tipo", "valor"])
    if df.empty:
        total_entradas = 0.0
        total_saidas = 0.0
    else:
        total_entradas = float(df.loc[df["tipo"] == TipoTransacao.entrada.value, "valor"].sum())
        total_saidas = float(df.loc[df["tipo"] == TipoTransacao.saida.value, "valor"].sum())

    return ResumoMensal(
        mes_ano=mes_ano,
        total_entradas=round(total_entradas, 2),
        total_saidas=round(total_saidas, 2),
        saldo_periodo=round(total_entradas - total_saidas, 2),
        saldo_total_contas=round(_saldo_total_contas(db), 2),
    )


def _linhas_por_categoria(
    db: Session, *, inicio: date | None = None, fim: date | None = None, tipos: list[TipoTransacao] | None = None
) -> list[Transacao]:
    stmt = select(Transacao).options(selectinload(Transacao.categorias))
    if inicio is not None and fim is not None:
        stmt = stmt.where(Transacao.data >= inicio, Transacao.data < fim)
    if tipos is not None:
        stmt = stmt.where(Transacao.tipo.in_(tipos))
    return list(db.execute(stmt).scalars().unique().all())


@router.get("/mensal", response_model=ResumoMensal)
def resumo_mensal(mes_ano: str | None = None, db: Session = Depends(get_db)) -> ResumoMensal:
    return _resumo_mensal(db, mes_ano or _mes_atual())


@router.get("/categorias", response_model=list[ResumoCategoria])
def resumo_categorias(mes_ano: str | None = None, db: Session = Depends(get_db)) -> list[ResumoCategoria]:
    inicio, fim = limites_mes(mes_ano or _mes_atual())
    transacoes = _linhas_por_categoria(db, inicio=inicio, fim=fim, tipos=[TipoTransacao.saida])

    # Assunção: uma transação vinculada a N categorias tem seu valor
    # dividido igualmente entre elas (1/N por categoria) para fins desta
    # agregação, em vez de contar o valor cheio em cada categoria (o que
    # infracionaria o total geral de saídas do mês).
    linhas = []
    for t in transacoes:
        valor = float(t.valor)
        categorias = t.categorias
        if not categorias:
            linhas.append({"categoria_id": None, "nome": SEM_CATEGORIA_NOME, "valor": valor})
        else:
            fatia = valor / len(categorias)
            for c in categorias:
                linhas.append({"categoria_id": c.id, "nome": c.nome, "valor": fatia})

    if not linhas:
        return []

    df = pd.DataFrame(linhas)
    total = float(df["valor"].sum())
    agrupado = df.groupby(["categoria_id", "nome"], dropna=False)["valor"].sum().reset_index()

    resultado = []
    for _, row in agrupado.iterrows():
        valor_total = float(row["valor"])
        categoria_id = row["categoria_id"]
        resultado.append(
            ResumoCategoria(
                categoria_id=None if pd.isna(categoria_id) else int(categoria_id),
                nome=row["nome"],
                total=round(valor_total, 2),
                percentual=round((valor_total / total * 100) if total else 0.0, 2),
            )
        )
    return resultado


@router.get("/categorias/total")
def resumo_categorias_total(db: Session = Depends(get_db)) -> list[dict]:
    separado = obter_valor_config(db, "total_categoria_separado")
    transacoes = _linhas_por_categoria(db)

    # Mesma assunção de divisão igualitária do valor entre categorias
    # vinculadas usada em /resumo/categorias, aplicada aqui a entradas e
    # saídas de todos os tempos.
    linhas = []
    for t in transacoes:
        valor = float(t.valor)
        categorias = t.categorias
        alvo: list = categorias if categorias else [None]
        fatia = valor / len(alvo)
        for c in alvo:
            linhas.append(
                {
                    "categoria_id": c.id if c is not None else None,
                    "nome": c.nome if c is not None else SEM_CATEGORIA_NOME,
                    "valor_entrada": fatia if t.tipo == TipoTransacao.entrada else 0.0,
                    "valor_saida": fatia if t.tipo == TipoTransacao.saida else 0.0,
                }
            )

    if not linhas:
        return []

    df = pd.DataFrame(linhas)
    agrupado = (
        df.groupby(["categoria_id", "nome"], dropna=False)[["valor_entrada", "valor_saida"]]
        .sum()
        .reset_index()
    )

    resultado = []
    for _, row in agrupado.iterrows():
        categoria_id = row["categoria_id"]
        item: dict = {
            "categoria_id": None if pd.isna(categoria_id) else int(categoria_id),
            "nome": row["nome"],
        }
        entrada = float(row["valor_entrada"])
        saida = float(row["valor_saida"])
        if separado:
            item["total_entrada"] = round(entrada, 2)
            item["total_saida"] = round(saida, 2)
        else:
            item["total"] = round(entrada - saida, 2)
        resultado.append(item)
    return resultado


def _variacao_percentual(base: float, atual: float) -> float | None:
    # Sem uma base anterior (mes1 == 0), a variação percentual não é
    # matematicamente definida — devolve None (não 0%, que significaria
    # "sem mudança") em vez de levantar erro ou devolver infinito.
    if base == 0:
        return None
    return round((atual - base) / base * 100, 2)


@router.get("/comparativo", response_model=ResumoComparativo)
def resumo_comparativo(mes1: str, mes2: str, db: Session = Depends(get_db)) -> ResumoComparativo:
    resumo1 = _resumo_mensal(db, mes1)
    resumo2 = _resumo_mensal(db, mes2)
    return ResumoComparativo(
        mes1=resumo1,
        mes2=resumo2,
        variacao_percentual=VariacaoPercentual(
            total_entradas=_variacao_percentual(resumo1.total_entradas, resumo2.total_entradas),
            total_saidas=_variacao_percentual(resumo1.total_saidas, resumo2.total_saidas),
        ),
    )
