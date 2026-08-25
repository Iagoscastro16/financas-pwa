from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import (
    AUTH_PASSWORD_HASH,
    AUTH_USERNAME,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Não foi possível validar as credenciais",
    headers={"WWW-Authenticate": "Bearer"},
)

LOGIN_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Usuário ou senha inválidos",
)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def authenticate_user(username: str, password: str) -> bool:
    if username != AUTH_USERNAME:
        # Ainda assim executa o verify para evitar diferença de tempo entre
        # usuário inexistente e senha incorreta (mitiga timing attack).
        pwd_context.verify(password, AUTH_PASSWORD_HASH)
        return False
    return verify_password(password, AUTH_PASSWORD_HASH)


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise CREDENTIALS_EXCEPTION
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise CREDENTIALS_EXCEPTION from exc

    username = payload.get("sub")
    if username is None or username != AUTH_USERNAME:
        raise CREDENTIALS_EXCEPTION
    return username
