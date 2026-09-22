"""add transacao_recorrente

Revision ID: 25346aea8904
Revises: cf0d3a2ab2ce
Create Date: 2026-09-21 20:43:50.499384

NOTE: adjusted from the raw autogenerate output — `op.create_foreign_key`/
`op.drop_constraint` outside of batch mode aren't supported on SQLite (it
has no `ALTER TABLE ADD/DROP CONSTRAINT`), so the `transacao.recorrencia_id`
column + its FK are added/dropped via `batch_alter_table`, same pattern used
in 5d3a2c4ed1b0/cf0d3a2ab2ce. The FK is given an explicit name so it can be
targeted by name in `downgrade()` (autogenerate's `None` name relies on
batch mode's own reflection to find it, which only works for drops, not for
naming it at creation time).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25346aea8904'
down_revision: Union[str, Sequence[str], None] = 'cf0d3a2ab2ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('transacao_recorrente',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=255), nullable=False),
    sa.Column('valor', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('tipo', sa.Enum('entrada', 'saida', name='tipotransacao'), nullable=False),
    sa.Column('conta_id', sa.Integer(), nullable=False),
    sa.Column('dia_mes', sa.Integer(), nullable=False),
    sa.Column('data_inicio', sa.Date(), nullable=False),
    sa.Column('data_fim', sa.Date(), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('ultima_geracao', sa.Date(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['conta_id'], ['conta.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transacao_recorrente_categoria',
    sa.Column('transacao_recorrente_id', sa.Integer(), nullable=False),
    sa.Column('categoria_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['categoria_id'], ['categoria.id'], ),
    sa.ForeignKeyConstraint(['transacao_recorrente_id'], ['transacao_recorrente.id'], ),
    sa.PrimaryKeyConstraint('transacao_recorrente_id', 'categoria_id')
    )
    with op.batch_alter_table('transacao') as batch_op:
        batch_op.add_column(sa.Column('recorrencia_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_transacao_recorrencia_id',
            'transacao_recorrente',
            ['recorrencia_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('transacao') as batch_op:
        batch_op.drop_constraint('fk_transacao_recorrencia_id', type_='foreignkey')
        batch_op.drop_column('recorrencia_id')
    op.drop_table('transacao_recorrente_categoria')
    op.drop_table('transacao_recorrente')
