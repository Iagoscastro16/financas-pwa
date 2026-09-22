import os

import app.scheduler as scheduler_module
from app.database import Base


def test_scheduler_desabilitado_em_testes_nao_inicia_nada():
    # DISABLE_SCHEDULER=true é setado globalmente em conftest.py: nenhum
    # teste deve acidentalmente acionar o scheduler real contra o engine
    # global (que não tem tabelas criadas em ambiente de teste).
    assert os.environ.get("DISABLE_SCHEDULER") == "true"
    resultado = scheduler_module.iniciar_scheduler()
    assert resultado is None
    assert scheduler_module._scheduler is None


def test_iniciar_scheduler_duas_vezes_nao_duplica_job(monkeypatch, db_engine):
    """Simula o cenário de reload: `iniciar_scheduler()` chamado de novo sem
    um `parar_scheduler()` correspondente nunca deve resultar em dois jobs
    (ou dois schedulers) rodando a geração de recorrências ao mesmo tempo."""
    Base.metadata.create_all(bind=db_engine)
    from sqlalchemy.orm import sessionmaker

    session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    monkeypatch.setattr(scheduler_module, "SessionLocal", session_local)
    monkeypatch.delenv("DISABLE_SCHEDULER", raising=False)

    try:
        primeiro = scheduler_module.iniciar_scheduler()
        segundo = scheduler_module.iniciar_scheduler()

        assert primeiro is segundo
        assert len(primeiro.get_jobs()) == 1
        assert primeiro.get_job(scheduler_module.JOB_ID) is not None
    finally:
        scheduler_module.parar_scheduler()

    assert scheduler_module._scheduler is None
