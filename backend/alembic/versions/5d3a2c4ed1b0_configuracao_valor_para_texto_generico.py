"""configuracao valor para texto generico

Revision ID: 5d3a2c4ed1b0
Revises: e8b04cc4e1d4
Create Date: 2026-08-26 23:42:10.048078

Converte `configuracao.valor` de Boolean para texto genérico, para poder
guardar bool, número ou texto livre sem precisar de uma nova coluna/migração
a cada novo tipo de configuração (interpretação de tipo passa a ser
responsabilidade de quem lê cada chave — ver app/routers/configuracao.py).

Isto é uma migração de DADOS, não só de schema: linhas existentes (True/False)
são convertidas para as strings literais "true"/"false", preservando o
significado original em vez de só trocar o tipo da coluna.

SQLite não suporta ALTER COLUMN de tipo diretamente, então usamos o padrão
"adicionar coluna nova + copiar dado convertido + dropar a antiga" via
`batch_alter_table` (que faz isso através de uma recriação de tabela).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d3a2c4ed1b0'
down_revision: Union[str, Sequence[str], None] = 'e8b04cc4e1d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema + dados: bool -> string ("true"/"false")."""
    with op.batch_alter_table('configuracao') as batch_op:
        batch_op.add_column(sa.Column('valor_str', sa.Text(), nullable=True))

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE configuracao SET valor_str = CASE WHEN valor THEN 'true' ELSE 'false' END"
        )
    )

    with op.batch_alter_table('configuracao') as batch_op:
        batch_op.drop_column('valor')
        batch_op.alter_column('valor_str', new_column_name='valor', nullable=False)


def downgrade() -> None:
    """Downgrade schema + dados: string -> bool.

    Só "true"/"false" (case-insensitive) têm conversão sensata para boolean.
    Qualquer outra chave gravada nesse meio-tempo (ex.: um valor numérico
    como "80" para orcamento_limite_alerta_percentual) NÃO tem um booleano
    correspondente razoável — em vez de silenciosamente corromper esses
    valores (ex.: transformando "80" em False), o downgrade levanta um erro
    e exige limpeza manual dessas linhas antes de prosseguir.
    """
    conn = op.get_bind()
    invalidas = conn.execute(
        sa.text("SELECT chave, valor FROM configuracao WHERE lower(valor) NOT IN ('true', 'false')")
    ).fetchall()
    if invalidas:
        descricao = ", ".join(f"{chave}={valor!r}" for chave, valor in invalidas)
        raise RuntimeError(
            "Não é possível fazer downgrade de 'configuracao.valor' para boolean: "
            f"as seguintes chaves têm valores não-booleanos e seriam corrompidas: {descricao}. "
            "Remova ou corrija manualmente essas linhas antes de rodar o downgrade."
        )

    with op.batch_alter_table('configuracao') as batch_op:
        batch_op.add_column(sa.Column('valor_bool', sa.Boolean(), nullable=True))

    conn.execute(
        sa.text("UPDATE configuracao SET valor_bool = CASE WHEN lower(valor) = 'true' THEN 1 ELSE 0 END")
    )

    with op.batch_alter_table('configuracao') as batch_op:
        batch_op.drop_column('valor')
        batch_op.alter_column('valor_bool', new_column_name='valor', nullable=False)
