"""Testes específicos da migração cf0d3a2ab2ce (transacao.data: Date ->
DateTime), rodando o Alembic de verdade via subprocess contra um arquivo
SQLite descartável — não usa o engine em memória compartilhado dos outros
testes (app/database.py), já que Alembic precisa de um arquivo real para as
operações de batch_alter_table (recriação de tabela) da migração.

Existe especificamente porque a primeira versão desta migração usava
`batch_op.alter_column(type_=sa.DateTime())` direto, e o SQLite corrompia
os valores existentes ("2026-08-15" virava o inteiro 2026) por causa de
como o modo batch copia dados via `CAST(data AS DATETIME)` — ver o
docstring da migração para detalhes. Os testes com banco em memória
(create_all) nunca passam pela migração de verdade, então não pegam esse
tipo de bug de corrupção de dado durante o ALTER."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
REVISAO_ANTERIOR = "5d3a2c4ed1b0"
REVISAO_MIGRACAO = "cf0d3a2ab2ce"


def _alembic(db_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"},
        capture_output=True,
        text=True,
        timeout=30,
    )


def _versao_atual(db_path: Path) -> str:
    con = sqlite3.connect(db_path)
    try:
        return con.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    finally:
        con.close()


@pytest.fixture()
def db_na_revisao_anterior(tmp_path):
    """Banco novo, parado na revisão imediatamente ANTES desta migração
    (transacao.data ainda Date)."""
    db_path = tmp_path / "migration_test.db"
    resultado = _alembic(db_path, "upgrade", REVISAO_ANTERIOR)
    assert resultado.returncode == 0, resultado.stderr
    return db_path


def _inserir_transacao(db_path: Path, transacao_id: int, data: str) -> None:
    con = sqlite3.connect(db_path)
    con.execute(
        "INSERT INTO conta (id, nome, saldo_inicial, ativo) VALUES (1, 'Conta', 0, 1)"
    )
    con.execute(
        "INSERT INTO transacao (id, conta_id, tipo, valor, data) VALUES (?, 1, 'saida', 10, ?)",
        (transacao_id, data),
    )
    con.commit()
    con.close()


def test_upgrade_preserva_data_existente_como_meia_noite(db_na_revisao_anterior):
    _inserir_transacao(db_na_revisao_anterior, 1, "2026-08-15")

    resultado = _alembic(db_na_revisao_anterior, "upgrade", REVISAO_MIGRACAO)
    assert resultado.returncode == 0, resultado.stderr
    assert _versao_atual(db_na_revisao_anterior) == REVISAO_MIGRACAO

    con = sqlite3.connect(db_na_revisao_anterior)
    valor, tipo = con.execute(
        "SELECT data, typeof(data) FROM transacao WHERE id = 1"
    ).fetchone()
    con.close()

    # Regressão: uma implementação anterior desta migração usava
    # `alter_column(type_=...)` direto, e o CAST do SQLite corrompia a data
    # para o inteiro 2026 em vez de preservar "2026-08-15".
    assert tipo == "text"
    assert valor == "2026-08-15"


def test_upgrade_com_banco_vazio_nao_falha(db_na_revisao_anterior):
    resultado = _alembic(db_na_revisao_anterior, "upgrade", REVISAO_MIGRACAO)
    assert resultado.returncode == 0, resultado.stderr
    assert _versao_atual(db_na_revisao_anterior) == REVISAO_MIGRACAO


def test_downgrade_trunca_horario_de_volta_para_data(db_na_revisao_anterior):
    _inserir_transacao(db_na_revisao_anterior, 1, "2026-08-15")
    assert _alembic(db_na_revisao_anterior, "upgrade", REVISAO_MIGRACAO).returncode == 0

    con = sqlite3.connect(db_na_revisao_anterior)
    con.execute("UPDATE transacao SET data = '2026-08-15 15:30:00.000000' WHERE id = 1")
    con.commit()
    con.close()

    resultado = _alembic(db_na_revisao_anterior, "downgrade", REVISAO_ANTERIOR)
    assert resultado.returncode == 0, resultado.stderr
    assert _versao_atual(db_na_revisao_anterior) == REVISAO_ANTERIOR

    con = sqlite3.connect(db_na_revisao_anterior)
    valor, tipo = con.execute(
        "SELECT data, typeof(data) FROM transacao WHERE id = 1"
    ).fetchone()
    con.close()
    assert tipo == "text"
    assert valor == "2026-08-15"
