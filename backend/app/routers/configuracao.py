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

# `Configuracao.valor` é sempre TEXT no banco (ver app/models/configuracao.py).
# Este router decide, por chave, como esse texto aparece na API:
#
# - Chaves em CHAVES_BOOLEANAS: armazenadas como "true"/"false", expostas na
#   API como bool — preserva o contrato existente (ex.: total_categoria_separado,
#   consumido por app.routers.resumo.obter_valor_config).
# - Qualquer outra chave: texto genérico, exposta como str na API. Chaves
#   numéricas conhecidas (ex.: percentuais) têm sua faixa validada na escrita
#   via FAIXAS_NUMERICAS, mas continuam armazenadas/expostas como string —
#   quem lê (ex.: futuro alerta de orçamento) converte para número.
CHAVES_BOOLEANAS = {"total_categoria_separado"}

# (mínimo, máximo) aceitos para chaves numéricas conhecidas, validados no PUT.
FAIXAS_NUMERICAS: dict[str, tuple[float, float]] = {
    # Percentual do limite do orçamento a partir do qual um alerta deve ser
    # disparado (ex.: "80" = avisar ao atingir 80% do valor_maximo).
    "orcamento_limite_alerta_percentual": (1, 100),
}

# Defaults hardcoded usados quando uma chave nunca foi explicitamente gravada
# no banco. Já no tipo esperado pela API (bool ou str), não na codificação
# interna de armazenamento.
DEFAULTS: dict[str, bool | str] = {
    "total_categoria_separado": False,
    "orcamento_limite_alerta_percentual": "80",
}


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _string_para_bool(valor: str) -> bool:
    return valor.strip().lower() == "true"


def _bool_para_string(valor: bool) -> str:
    return "true" if valor else "false"


def _decodificar_valor(chave: str, valor_armazenado: str) -> bool | str:
    """Converte o texto bruto do banco para o tipo exposto pela API."""
    if chave in CHAVES_BOOLEANAS:
        return _string_para_bool(valor_armazenado)
    return valor_armazenado


def _validar_e_codificar(chave: str, valor: bool | str) -> str:
    """Valida `valor` de acordo com o tipo esperado para `chave` e devolve a
    representação em texto a ser persistida. Levanta 422 em caso de tipo
    incompatível ou (para chaves numéricas conhecidas) valor fora da faixa
    ou não numérico."""
    if chave in CHAVES_BOOLEANAS:
        if not isinstance(valor, bool):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"'{chave}' espera um valor booleano (true/false).",
            )
        return _bool_para_string(valor)

    if not isinstance(valor, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"'{chave}' espera um valor em texto.",
        )

    faixa = FAIXAS_NUMERICAS.get(chave)
    if faixa is not None:
        minimo, maximo = faixa
        try:
            numero = float(valor)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"'{chave}' deve ser um número entre {minimo:g} e {maximo:g}.",
            ) from exc
        if not (minimo <= numero <= maximo):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"'{chave}' deve ser um número entre {minimo:g} e {maximo:g}.",
            )

    return valor


def _para_leitura(configuracao: Configuracao) -> ConfiguracaoRead:
    return ConfiguracaoRead(
        chave=configuracao.chave,
        valor=_decodificar_valor(configuracao.chave, configuracao.valor),
        atualizado_em=configuracao.atualizado_em,
    )


def obter_valor_config(db: Session, chave: str) -> bool:
    """Lê o valor de uma chave de configuração BOOLEANA (ex.:
    total_categoria_separado) já decodificado, caindo no default hardcoded
    quando a chave nunca foi definida. Uso interno (ex.: app.routers.resumo)
    — não deve ser usado para chaves não booleanas."""
    configuracao = db.get(Configuracao, chave)
    if configuracao is not None:
        return _string_para_bool(configuracao.valor)
    default = DEFAULTS.get(chave, False)
    return default if isinstance(default, bool) else _string_para_bool(str(default))


@router.get("", response_model=list[ConfiguracaoRead])
def listar_configuracoes(db: Session = Depends(get_db)) -> list[ConfiguracaoRead]:
    linhas = db.execute(select(Configuracao)).scalars().all()
    return [_para_leitura(c) for c in linhas]


@router.get("/{chave}", response_model=ConfiguracaoRead)
def obter_configuracao(chave: str, db: Session = Depends(get_db)) -> ConfiguracaoRead:
    configuracao = db.get(Configuracao, chave)
    if configuracao is not None:
        return _para_leitura(configuracao)
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
) -> ConfiguracaoRead:
    valor_codificado = _validar_e_codificar(chave, payload.valor)

    configuracao = db.get(Configuracao, chave)
    valor_antigo = (
        _decodificar_valor(chave, configuracao.valor) if configuracao is not None else DEFAULTS.get(chave)
    )
    if configuracao is None:
        configuracao = Configuracao(chave=chave, valor=valor_codificado)
        db.add(configuracao)
    else:
        configuracao.valor = valor_codificado
    db.commit()
    db.refresh(configuracao)

    registrar_auditoria(
        usuario=current_user,
        acao="update",
        entidade="configuracao",
        entidade_id=None,
        detalhes={
            "chave": chave,
            "valor_antigo": valor_antigo,
            "valor_novo": _decodificar_valor(chave, configuracao.valor),
        },
        ip_origem=_ip(request),
    )
    return _para_leitura(configuracao)
