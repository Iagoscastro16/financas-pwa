from datetime import date

import pytest
from sqlalchemy.orm import sessionmaker

from app.models.categoria import Categoria
from app.models.conta import Conta
from app.models.transacao import TipoTransacao, Transacao
from app.models.transacao_recorrente import TransacaoRecorrente
from app.recorrencia import (
    data_ocorrencia_no_mes,
    gerar_ocorrencia_se_devida,
    processar_todas_as_regras,
)


@pytest.fixture()
def db_session(db_engine):
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def conta(db_session):
    conta = Conta(nome="Conta de teste")
    db_session.add(conta)
    db_session.commit()
    db_session.refresh(conta)
    return conta


def _criar_regra(db_session, conta, **overrides) -> TransacaoRecorrente:
    dados = dict(
        nome="Aluguel",
        valor=1000,
        tipo=TipoTransacao.saida,
        conta_id=conta.id,
        dia_mes=10,
        data_inicio=date(2020, 1, 1),
        data_fim=None,
        ativo=True,
    )
    dados.update(overrides)
    regra = TransacaoRecorrente(**dados)
    db_session.add(regra)
    db_session.commit()
    db_session.refresh(regra)
    return regra


# --- clamping de dia-do-mês ---


def test_data_ocorrencia_no_mes_dia_existe_no_mes():
    assert data_ocorrencia_no_mes(15, 2026, 3) == date(2026, 3, 15)


def test_data_ocorrencia_no_mes_dia_31_em_mes_de_30_dias_usa_ultimo_dia():
    assert data_ocorrencia_no_mes(31, 2026, 4) == date(2026, 4, 30)


def test_data_ocorrencia_no_mes_fevereiro_nao_bissexto_usa_ultimo_dia():
    assert data_ocorrencia_no_mes(29, 2026, 2) == date(2026, 2, 28)
    assert data_ocorrencia_no_mes(30, 2026, 2) == date(2026, 2, 28)
    assert data_ocorrencia_no_mes(31, 2026, 2) == date(2026, 2, 28)


def test_data_ocorrencia_no_mes_fevereiro_bissexto_usa_29():
    assert data_ocorrencia_no_mes(29, 2024, 2) == date(2024, 2, 29)
    assert data_ocorrencia_no_mes(30, 2024, 2) == date(2024, 2, 29)
    assert data_ocorrencia_no_mes(31, 2024, 2) == date(2024, 2, 29)


# --- gerar_ocorrencia_se_devida ---


def test_gera_quando_dia_ja_passou_no_mes(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=10)
    transacao = gerar_ocorrencia_se_devida(db_session, regra, date(2026, 3, 15))
    assert transacao is not None
    assert transacao.data.date() == date(2026, 3, 10)
    assert transacao.conta_id == conta.id
    assert transacao.tipo == TipoTransacao.saida
    assert transacao.recorrencia_id == regra.id
    assert regra.ultima_geracao == date(2026, 3, 10)


def test_gera_quando_dia_e_exatamente_hoje(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=15)
    transacao = gerar_ocorrencia_se_devida(db_session, regra, date(2026, 3, 15))
    assert transacao is not None
    assert regra.ultima_geracao == date(2026, 3, 15)


def test_nao_gera_quando_dia_ainda_nao_chegou_no_mes(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=20)
    transacao = gerar_ocorrencia_se_devida(db_session, regra, date(2026, 3, 15))
    assert transacao is None
    assert regra.ultima_geracao is None


def test_copia_categorias_da_regra_para_a_transacao_gerada(db_session, conta):
    categoria = Categoria(nome="Moradia", tipo="despesa")
    db_session.add(categoria)
    db_session.commit()
    db_session.refresh(categoria)

    regra = _criar_regra(db_session, conta, dia_mes=10)
    regra.categorias = [categoria]
    db_session.commit()

    transacao = gerar_ocorrencia_se_devida(db_session, regra, date(2026, 3, 15))
    assert transacao is not None
    assert [c.id for c in transacao.categorias] == [categoria.id]


def test_idempotencia_chamar_geracao_duas_vezes_nao_duplica(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=10)
    hoje = date(2026, 3, 15)

    primeira = gerar_ocorrencia_se_devida(db_session, regra, hoje)
    segunda = gerar_ocorrencia_se_devida(db_session, regra, hoje)

    assert primeira is not None
    assert segunda is None
    total = db_session.query(Transacao).filter_by(recorrencia_id=regra.id).count()
    assert total == 1


def test_respeita_data_fim_nao_gera_apos_o_fim(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=10, data_fim=date(2026, 2, 28))
    transacao = gerar_ocorrencia_se_devida(db_session, regra, date(2026, 3, 15))
    assert transacao is None
    assert regra.ultima_geracao is None


def test_respeita_data_fim_ainda_gera_ate_o_fim(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=10, data_fim=date(2026, 3, 31))
    transacao = gerar_ocorrencia_se_devida(db_session, regra, date(2026, 3, 15))
    assert transacao is not None


def test_regra_inativa_nunca_gera(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=10, ativo=False)
    transacao = gerar_ocorrencia_se_devida(db_session, regra, date(2026, 3, 15))
    assert transacao is None


def test_nao_gera_antes_da_data_inicio(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=10, data_inicio=date(2026, 4, 1))
    transacao = gerar_ocorrencia_se_devida(db_session, regra, date(2026, 3, 15))
    assert transacao is None


# --- processar_todas_as_regras (núcleo do job do scheduler) ---


def test_processar_todas_as_regras_pula_inativas_e_encerradas(db_session, conta):
    ativa = _criar_regra(db_session, conta, dia_mes=10, nome="Ativa")
    _criar_regra(db_session, conta, dia_mes=10, nome="Inativa", ativo=False)
    _criar_regra(
        db_session, conta, dia_mes=10, nome="Encerrada", data_fim=date(2026, 1, 1)
    )

    geradas = processar_todas_as_regras(db_session, date(2026, 3, 15))

    assert len(geradas) == 1
    assert geradas[0].recorrencia_id == ativa.id


def test_processar_todas_as_regras_idempotente_entre_duas_execucoes(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=10)
    hoje = date(2026, 3, 15)

    primeira_rodada = processar_todas_as_regras(db_session, hoje)
    segunda_rodada = processar_todas_as_regras(db_session, hoje)

    assert len(primeira_rodada) == 1
    assert len(segunda_rodada) == 0
    total = db_session.query(Transacao).filter_by(recorrencia_id=regra.id).count()
    assert total == 1


def test_processar_todas_as_regras_gera_de_novo_no_mes_seguinte(db_session, conta):
    regra = _criar_regra(db_session, conta, dia_mes=10)

    processar_todas_as_regras(db_session, date(2026, 3, 15))
    processar_todas_as_regras(db_session, date(2026, 4, 15))

    total = db_session.query(Transacao).filter_by(recorrencia_id=regra.id).count()
    assert total == 2
