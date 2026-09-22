import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.recorrencia import processar_todas_as_regras

logger = logging.getLogger(__name__)

JOB_ID = "gerar_transacoes_recorrentes"
INTERVALO_HORAS = 24

_scheduler: BackgroundScheduler | None = None


def executar_geracao_recorrencias() -> None:
    db = SessionLocal()
    try:
        geradas = processar_todas_as_regras(db)
        if geradas:
            logger.info("Geração de recorrências: %d transação(ões) criada(s)", len(geradas))
    except Exception:  # noqa: BLE001 — job de background nunca pode propagar e derrubar o processo
        logger.exception("Falha ao executar geração de transações recorrentes")
    finally:
        db.close()


def iniciar_scheduler() -> BackgroundScheduler | None:
    """Inicia o scheduler dentro do lifespan da aplicação (chamado no
    startup do FastAPI, uma vez por processo).

    Guardas contra duplicação de job, em particular sob `uvicorn --reload`:

    - O `--reload` do uvicorn não roda duas instâncias do processo ao mesmo
      tempo: ao detectar mudança de arquivo, ele encerra o processo atual
      (disparando o shutdown do lifespan → `parar_scheduler()`) e só depois
      sobe um processo novo (novo startup → `iniciar_scheduler()`). Como o
      scheduler só é criado dentro do lifespan (nunca em import de módulo) e
      é sempre parado no shutdown, cada reload troca uma instância pela
      outra em vez de acumular threads.
    - Singleton de módulo (`_scheduler`): se por algum motivo o startup for
      re-entrado no mesmo processo sem um shutdown correspondente, o
      scheduler já em execução é reaproveitado em vez de duplicado.
    - `add_job(..., id=JOB_ID, replace_existing=True)`: garante um único job
      agendado para essa tarefa mesmo que `add_job` seja chamado mais de uma
      vez sobre a mesma instância.
    - Em testes, `DISABLE_SCHEDULER=true` (setado em tests/conftest.py antes
      de importar `app.main`) faz o scheduler nem ser criado — os testes de
      geração chamam `processar_todas_as_regras`/`gerar_ocorrencia_se_devida`
      diretamente contra a sessão de teste isolada, sem depender do engine
      global que este módulo usa.
    """
    global _scheduler

    if os.environ.get("DISABLE_SCHEDULER") == "true":
        logger.info("Scheduler de recorrências desabilitado (DISABLE_SCHEDULER=true)")
        return None

    if _scheduler is not None and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        executar_geracao_recorrencias,
        "interval",
        hours=INTERVALO_HORAS,
        id=JOB_ID,
        replace_existing=True,
    )
    _scheduler.start()
    # Roda uma vez imediatamente no startup, para cobrir o período em que o
    # servidor ficou fora do ar (systemd) sem esperar o primeiro tick de 24h.
    executar_geracao_recorrencias()
    return _scheduler


def parar_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
