# Backend — Finanças API

API FastAPI + SQLAlchemy para o app de finanças pessoais.

## Bancos de dados

O backend usa **dois** bancos SQLite (cada um com seu próprio `Base`/engine):

- `financas.db` — dados da aplicação (`conta`, `categoria`, `transacao`,
  `transacao_categoria`, `orcamento`, `meta`). Engine/URL em
  `app/database.py` (`DATABASE_URL`).
- `auditoria.db` — log de auditoria append-only (`log_auditoria`), isolado do
  banco principal de propósito. Engine/URL em `app/audit_database.py`
  (`AUDIT_DATABASE_URL`).

Cada um tem seu **próprio ambiente Alembic**, já que são bases/engines
distintas com ciclos de vida independentes (o log de auditoria, inclusive,
tem candidatura a migrar para uma instância Postgres separada no futuro — ver
comentário em `app/audit_database.py`). Um único `env.py` compartilhado
tentando alternar entre duas `MetaData` diferentes seria mais confuso do que
manter dois setups simples e paralelos.

| | Banco principal | Auditoria |
|---|---|---|
| Config | `alembic.ini` | `alembic_audit.ini` |
| Scripts | `alembic/` | `alembic_audit/` |
| Comando | `alembic ...` | `alembic -c alembic_audit.ini ...` |

Ambos os `env.py` importam o `engine`/`Base` (ou `audit_engine`/`AuditBase`)
diretamente de `app/database.py` / `app/audit_database.py` — a string de
conexão (e o `.env`) só existe em um lugar, o Alembic não a duplica.

## Workflow do dia a dia

### Depois de alterar um model

```bash
# banco principal (app/models/*.py)
alembic revision --autogenerate -m "descreva a mudança"

# banco de auditoria (app/models/log_auditoria.py)
alembic -c alembic_audit.ini revision --autogenerate -m "descreva a mudança"
```

Sempre **revise o arquivo gerado** em `alembic/versions/` (ou
`alembic_audit/versions/`) antes de aplicar — autogenerate detecta a maioria
das mudanças de schema, mas não tudo (ex.: renomear coluna vira
drop+add por padrão).

### Aplicar migrações pendentes

```bash
alembic upgrade head                        # banco principal
alembic -c alembic_audit.ini upgrade head    # banco de auditoria
```

### Clone novo (banco ainda não existe)

Rodar `alembic upgrade head` (e o equivalente para auditoria) cria o arquivo
`.db` do zero, já no schema mais atual — não é mais necessário nenhum
`create_all` manual, `main.py` não cria mais tabelas em runtime.

### Banco de dev já existente (criado antes do Alembic)

Se você já tem um `financas.db`/`auditoria.db` local criado pela versão
antiga do app (via `Base.metadata.create_all`), **não rode `upgrade head`
direto** — a migração baseline tentaria criar tabelas que já existem e
falharia. Em vez disso, marque o banco como já estando na revisão baseline,
sem tocar no schema:

```bash
alembic stamp head                        # banco principal
alembic -c alembic_audit.ini stamp head   # banco de auditoria
```

Depois disso, `alembic upgrade head` em ambos passa a ser um no-op (até a
próxima migração real ser criada).

## Testes

A suíte de testes (`tests/`) **não** usa Alembic — cada teste roda contra um
SQLite em memória criado via `Base.metadata.create_all` (fixture `db_engine`
em `tests/conftest.py`), o que é mais rápido e isola os testes entre si sem
depender de arquivos de migração. Alembic é só para bancos reais
(dev/prod), como descrito acima.

```bash
pytest
```