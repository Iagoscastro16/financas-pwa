"""Testes específicos da migração 5d3a2c4ed1b0 (configuracao.valor:
Boolean -> Text), rodando o Alembic de verdade via subprocess contra um
arquivo SQLite descartável — não usa o engine em memória compartilhado dos
outros testes (app/database.py), já que Alembic precisa de um arquivo real
para as operações de batch_alter_table (recriação de tabela) da migração."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
REVISAO_ANTERIOR = "e8b04cc4e1d4"
REVISAO_MIGRACAO = "5d3a2c4ed1b0"


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
    (configuracao.valor ainda Boolean)."""
    db_path = tmp_path / "migration_test.db"
    resultado = _alembic(db_path, "upgrade", REVISAO_ANTERIOR)
    assert resultado.returncode == 0, resultado.stderr
    return db_path


def test_upgrade_converte_linhas_booleanas_existentes_para_string(db_na_revisao_anterior):
    con = sqlite3.connect(db_na_revisao_anterior)
    con.execute("INSERT INTO configuracao (chave, valor) VALUES ('total_categoria_separado', 1)")
    con.execute("INSERT INTO configuracao (chave, valor) VALUES ('outra_chave_false', 0)")
    con.commit()
    con.close()

    resultado = _alembic(db_na_revisao_anterior, "upgrade", REVISAO_MIGRACAO)
    assert resultado.returncode == 0, resultado.stderr
    assert _versao_atual(db_na_revisao_anterior) == REVISAO_MIGRACAO

    con = sqlite3.connect(db_na_revisao_anterior)
    valores = dict(con.execute("SELECT chave, valor FROM configuracao").fetchall())
    tipos = dict(con.execute("SELECT chave, typeof(valor) FROM configuracao").fetchall())
    con.close()

    assert valores == {"total_categoria_separado": "true", "outra_chave_false": "false"}
    assert tipos == {"total_categoria_separado": "text", "outra_chave_false": "text"}


def test_upgrade_com_banco_vazio_nao_falha(db_na_revisao_anterior):
    resultado = _alembic(db_na_revisao_anterior, "upgrade", REVISAO_MIGRACAO)
    assert resultado.returncode == 0, resultado.stderr
    assert _versao_atual(db_na_revisao_anterior) == REVISAO_MIGRACAO


def test_downgrade_restaura_boolean_a_partir_de_strings_validas(db_na_revisao_anterior):
    con = sqlite3.connect(db_na_revisao_anterior)
    con.execute("INSERT INTO configuracao (chave, valor) VALUES ('ligado', 1)")
    con.execute("INSERT INTO configuracao (chave, valor) VALUES ('desligado', 0)")
    con.commit()
    con.close()
    assert _alembic(db_na_revisao_anterior, "upgrade", "head").returncode == 0

    resultado = _alembic(db_na_revisao_anterior, "downgrade", REVISAO_ANTERIOR)
    assert resultado.returncode == 0, resultado.stderr
    assert _versao_atual(db_na_revisao_anterior) == REVISAO_ANTERIOR

    con = sqlite3.connect(db_na_revisao_anterior)
    linhas = con.execute("SELECT chave, valor, typeof(valor) FROM configuracao ORDER BY chave").fetchall()
    con.close()
    assert linhas == [("desligado", 0, "integer"), ("ligado", 1, "integer")]


def test_downgrade_recusa_apagar_valor_nao_booleano(db_na_revisao_anterior):
    assert _alembic(db_na_revisao_anterior, "upgrade", "head").returncode == 0

    con = sqlite3.connect(db_na_revisao_anterior)
    con.execute(
        "INSERT INTO configuracao (chave, valor) VALUES "
        "('orcamento_limite_alerta_percentual', '80')"
    )
    con.commit()
    con.close()

    resultado = _alembic(db_na_revisao_anterior, "downgrade", REVISAO_ANTERIOR)
    assert resultado.returncode != 0
    assert "orcamento_limite_alerta_percentual" in resultado.stderr

    # nada foi corrompido: o banco continua íntegro na revisão nova
    assert _versao_atual(db_na_revisao_anterior) == REVISAO_MIGRACAO
    con = sqlite3.connect(db_na_revisao_anterior)
    valor = con.execute(
        "SELECT valor FROM configuracao WHERE chave = 'orcamento_limite_alerta_percentual'"
    ).fetchone()[0]
    con.close()
    assert valor == "80"
