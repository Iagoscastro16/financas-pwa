from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Configuracao(Base):
    """Tabela de configurações chave/valor genérica: `valor` é sempre
    armazenado como texto (para acomodar bool, número ou texto livre sem
    precisar de nova coluna/migração a cada novo tipo de configuração) — a
    interpretação/conversão de tipo é responsabilidade de quem lê cada
    chave (ver app.routers.configuracao)."""

    __tablename__ = "configuracao"

    chave: Mapped[str] = mapped_column(String(100), primary_key=True)
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
