from fastapi import APIRouter, Request

from app.audit import registrar_auditoria
from app.auth import LOGIN_EXCEPTION, authenticate_user, create_access_token
from app.limiter import limiter
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest) -> TokenResponse:
    ip_origem = request.client.host if request.client else None

    if not authenticate_user(payload.username, payload.password):
        registrar_auditoria(
            usuario=payload.username,
            acao="login_failed",
            entidade="auth",
            detalhes={"motivo": "credenciais inválidas"},
            ip_origem=ip_origem,
        )
        raise LOGIN_EXCEPTION

    token = create_access_token(subject=payload.username)
    registrar_auditoria(
        usuario=payload.username,
        acao="login",
        entidade="auth",
        detalhes={"motivo": "login bem-sucedido"},
        ip_origem=ip_origem,
    )
    return TokenResponse(access_token=token)
