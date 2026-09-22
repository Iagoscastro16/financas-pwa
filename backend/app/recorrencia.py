import calendar
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transacao import Transacao
from app.models.transacao_recorrente import TransacaoRecorrente


def data_ocorrencia_no_mes(dia_mes: int, ano: int, mes: int) -> date:
    """Resolve o dia-do-mês configurado (1-31) para uma data real de um mês
    específico, "grudando" no último dia do mês quando `dia_mes` não existe
    nele (ex.: dia_mes=31 em fevereiro vira o último dia de fevereiro)."""
    ultimo_dia_do_mes = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia_mes, ultimo_dia_do_mes))


def gerar_ocorrencia_se_devida(
    db: Session, regra: TransacaoRecorrente, hoje: date | None = None
) -> Transacao | None:
    """Gera a transação do mês corrente para `regra`, se e somente se ainda
    não foi gerada e já estiver na data (ou no passado). Idempotente: chamar
    duas vezes na mesma janela mensal só gera uma vez, guiado por
    `ultima_geracao` — nunca varre `transacao` para descobrir isso.

    Retorna a transação criada, ou None se nada precisava ser gerado.
    """
    if hoje is None:
        hoje = date.today()

    if not regra.ativo:
        return None

    ocorrencia = data_ocorrencia_no_mes(regra.dia_mes, hoje.year, hoje.month)

    if ocorrencia < regra.data_inicio:
        return None
    if ocorrencia > hoje:
        return None
    if regra.data_fim is not None and ocorrencia > regra.data_fim:
        return None
    if (
        regra.ultima_geracao is not None
        and regra.ultima_geracao.year == ocorrencia.year
        and regra.ultima_geracao.month == ocorrencia.month
    ):
        return None

    transacao = Transacao(
        conta_id=regra.conta_id,
        tipo=regra.tipo,
        valor=regra.valor,
        data=datetime.combine(ocorrencia, datetime.min.time()),
        descricao=regra.nome,
        recorrencia_id=regra.id,
    )
    transacao.categorias = list(regra.categorias)
    db.add(transacao)
    regra.ultima_geracao = ocorrencia
    db.commit()
    db.refresh(transacao)
    return transacao


def processar_todas_as_regras(db: Session, hoje: date | None = None) -> list[Transacao]:
    """Roda `gerar_ocorrencia_se_devida` para toda regra ativa e não
    encerrada — usado pelo job diário do scheduler. Regras com `data_fim` já
    no passado são filtradas na própria query, então nem chegam a ser
    avaliadas mês a mês depois de encerradas."""
    if hoje is None:
        hoje = date.today()

    regras = (
        db.execute(
            select(TransacaoRecorrente).where(
                TransacaoRecorrente.ativo.is_(True),
                (TransacaoRecorrente.data_fim.is_(None)) | (TransacaoRecorrente.data_fim >= hoje),
            )
        )
        .scalars()
        .all()
    )

    geradas = []
    for regra in regras:
        transacao = gerar_ocorrencia_se_devida(db, regra, hoje)
        if transacao is not None:
            geradas.append(transacao)
    return geradas
