"""Logging técnico/operacional da aplicação (erros, start/stop, avisos de
bibliotecas) — para debugging e visibilidade operacional.

Isto é DIFERENTE do sistema de auditoria de negócio (app/audit.py,
registrar_auditoria, tabela log_auditoria em auditoria.db), que registra
ações de usuário (quem fez o quê) para fins de conformidade/rastreabilidade.
Os dois sistemas não se misturam: nada aqui grava em auditoria.db, e
registrar_auditoria não deve ser usado para eventos técnicos.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Caminho relativo ao projeto (backend/logs/), não absoluto (ex.: /var/log) —
# o destino de deployment ainda não está decidido.
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"

MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3


def _resolver_nivel() -> int:
    nivel_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    nivel = getattr(logging, nivel_str, None)
    return nivel if isinstance(nivel, int) else logging.INFO


def setup_logging() -> None:
    """Configura o logger raiz: nível (via LOG_LEVEL, default INFO), formato
    em texto plano com timestamp/nível/logger/mensagem, e dois handlers
    simultâneos — console (StreamHandler) e arquivo rotativo
    (backend/logs/app.log, 5MB x 3 backups).

    Deve ser chamada uma única vez, o mais cedo possível na inicialização do
    processo (ver app/main.py) — antes de qualquer outro import com efeito
    colateral, para que até falhas de inicialização fiquem registradas.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(_resolver_nivel())
    # Evita handlers duplicados/acumulados se setup_logging() for chamada
    # mais de uma vez no mesmo processo (ex.: reimportação em testes).
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # warnings.warn() de bibliotecas (ex.: DeprecationWarning do slowapi) por
    # padrão só vão para stderr via warnings.showwarning e ficam invisíveis
    # sob uvicorn (que não roda como __main__). Isto os redireciona para o
    # logger "py.warnings", passando pelos mesmos handlers acima.
    logging.captureWarnings(True)
