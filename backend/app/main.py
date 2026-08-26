from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import models  # noqa: F401  (garante que todos os modelos sejam registrados)
from app.audit_database import AuditBase, audit_engine
from app.database import Base, engine
from app.limiter import limiter
from app.models import log_auditoria  # noqa: F401  (registra o model de auditoria)
from app.routers import auditoria, auth, categorias, contas, metas, orcamentos, transacoes
from app.security_headers import add_security_headers

Base.metadata.create_all(bind=engine)
AuditBase.metadata.create_all(bind=audit_engine)

app = FastAPI(title="Finanças API")

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


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
