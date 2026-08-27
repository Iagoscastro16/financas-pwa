from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import registrar_auditoria
from app.auth import get_current_user
from app.database import get_db
from app.models.configuracao import Configuracao
from app.schemas.configuracao import ConfiguracaoRead, ConfiguracaoUpdate

router = APIRouter(
    prefix="/configuracao", tags=["configuracao"], dependencies=[Depends(get_current_user)]
)

# Defaults hardcoded usados quando uma chave nunca foi explicitamente gravada
# no banco. Também reutilizado por app.routers.resumo para ler configurações
# de agregação (ex.: "total_categoria_separado").
DEFAULTS: dict[str, bool] = {
    "total_categoria_separado": False,
}


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def obter_valor_config(db: Session, chave: str) -> bool:
    """Lê o valor booleano de uma chave de configuração, caindo no default
    hardcoded quando a chave nunca foi definida."""
    configuracao = db.get(Configuracao, chave)
    if configuracao is not None:
        return configuracao.valor
    return DEFAULTS.get(chave, False)


@router.get("", response_model=list[ConfiguracaoRead])
def listar_configuracoes(db: Session = Depends(get_db)) -> list[Configuracao]:
    return list(db.execute(select(Configuracao)).scalars().all())


@router.get("/{chave}", response_model=ConfiguracaoRead)
def obter_configuracao(chave: str, db: Session = Depends(get_db)) -> Configuracao | ConfiguracaoRead:
    configuracao = db.get(Configuracao, chave)
    if configuracao is not None:
        return configuracao
    if chave not in DEFAULTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuração desconhecida")
    return ConfiguracaoRead(chave=chave, valor=DEFAULTS[chave], atualizado_em=None)


@router.put("/{chave}", response_model=ConfiguracaoRead)
def atualizar_configuracao(
    chave: str,
    payload: ConfiguracaoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Configuracao:
    configuracao = db.get(Configuracao, chave)
    valor_antigo = configuracao.valor if configuracao is not None else DEFAULTS.get(chave)
    if configuracao is None:
        configuracao = Configuracao(chave=chave, valor=payload.valor)
        db.add(configuracao)
    else:
        configuracao.valor = payload.valor
    db.commit()
    db.refresh(configuracao)
    registrar_auditoria(
        usuario=current_user,
        acao="update",
        entidade="configuracao",
        entidade_id=None,
        detalhes={"chave": chave, "valor_antigo": valor_antigo, "valor_novo": configuracao.valor},
        ip_origem=_ip(request),
    )
    return configuracao
