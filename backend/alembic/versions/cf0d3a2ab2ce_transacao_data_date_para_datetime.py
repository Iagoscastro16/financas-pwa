"""transacao data date para datetime

Revision ID: cf0d3a2ab2ce
Revises: 5d3a2c4ed1b0
Create Date: 2026-08-29 00:00:00.000000

Converte `transacao.data` de Date para DateTime, para permitir registrar o
horário exato de uma transação (não só o dia). Linhas existentes não têm
horário real para recuperar (foram criadas antes desta mudança), então
ficam com a porção de horário zerada (00:00:00) — ou seja, a mesma data
que já tinham, só que agora representável como datetime.

IMPORTANTE — por que NÃO usamos `batch_op.alter_column(type_=sa.DateTime())`
direto: no SQLite, a recriação de tabela do modo batch copia a coluna via
`CAST(data AS DATETIME)`. O SQLite não reconhece "DATETIME" como um dos
tipos válidos de CAST (TEXT/REAL/INTEGER/NUMERIC/BLOB) e cai no fallback de
afinidade NUMERIC, que trunca a string ISO para só o prefixo numérico —
"2026-08-15" vira o inteiro 2026, corrompendo a data (verificado
empiricamente antes de escrever esta migração). Por isso usamos o mesmo
padrão de 5d3a2c4ed1b0 (adicionar coluna nova + copiar valor cru via
`UPDATE` sem CAST + dropar a antiga): a string "YYYY-MM-DD" já é um valor
válido de entrada para uma coluna DateTime (interpretada como meia-noite),
então copiar sem transformação preserva o valor corretamente.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf0d3a2ab2ce'
down_revision: Union[str, Sequence[str], None] = '5d3a2c4ed1b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('transacao') as batch_op:
        batch_op.add_column(sa.Column('data_datetime', sa.DateTime(), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("UPDATE transacao SET data_datetime = data"))

    with op.batch_alter_table('transacao') as batch_op:
        batch_op.drop_column('data')
        batch_op.alter_column('data_datetime', new_column_name='data', nullable=False)


def downgrade() -> None:
    # Trunca o horário de volta para meia-noite (perda de precisão
    # aceitável: Date nunca teve como guardar horário). O tipo Date do
    # SQLAlchemy/SQLite exige estritamente "YYYY-MM-DD" (ao contrário do
    # DateTime, que aceita a porção de hora ausente) — por isso usamos
    # `substr` para cortar os 10 primeiros caracteres em vez de copiar o
    # valor cru como no upgrade.
    with op.batch_alter_table('transacao') as batch_op:
        batch_op.add_column(sa.Column('data_date', sa.Date(), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("UPDATE transacao SET data_date = substr(data, 1, 10)"))

    with op.batch_alter_table('transacao') as batch_op:
        batch_op.drop_column('data')
        batch_op.alter_column('data_date', new_column_name='data', nullable=False)
