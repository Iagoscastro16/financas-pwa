from fastapi import APIRouter, Request

from app.auth import LOGIN_EXCEPTION, authenticate_user, create_access_token
from app.limiter import limiter
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest) -> TokenResponse:
    if not authenticate_user(payload.username, payload.password):
        raise LOGIN_EXCEPTION
    token = create_access_token(subject=payload.username)
    return TokenResponse(access_token=token)
