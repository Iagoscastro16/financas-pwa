from app.logging_config import setup_logging

# Chamado antes de qualquer outro import com efeito colateral (Base/engine
# do banco principal, setup do banco de auditoria etc.) — para que até
# falhas de inicialização apareçam no log.
setup_logging()

import logging  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402

from app import models  # noqa: E402,F401  (garante que todos os modelos sejam registrados)
from app.limiter import limiter  # noqa: E402
from app.models import log_auditoria  # noqa: E402,F401  (registra o model de auditoria)
from app.routers import (  # noqa: E402
    auditoria,
    auth,
    categorias,
    configuracao,
    contas,
    metas,
    orcamentos,
    resumo,
    transacoes,
)
from app.security_headers import add_security_headers  # noqa: E402

# Schema criado/atualizado via Alembic (ver backend/README.md), não mais em
# runtime: `alembic upgrade head` (financas.db) e
# `alembic -c alembic_audit.ini upgrade head` (auditoria.db).

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Aplicação iniciando")
    yield
    logger.info("Aplicação encerrando")


app = FastAPI(title="Finanças API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(add_security_headers)

app.include_router(auth.router)
app.include_router(contas.router)
app.include_router(categorias.router)
app.include_router(transacoes.router)
app.include_router(orcamentos.router)
app.include_router(metas.router)
app.include_router(auditoria.router)
app.include_router(configuracao.router)
app.include_router(resumo.router)


@app.exception_handler(Exception)
async def tratar_excecao_nao_capturada(request: Request, exc: Exception) -> JSONResponse:
    """Logging técnico (não é auditoria de negócio): grava o traceback
    completo no log operacional e devolve uma resposta 500 genérica — os
    detalhes internos nunca vazam para o cliente, só para o log."""
    logger.exception("Erro não tratado ao processar %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
