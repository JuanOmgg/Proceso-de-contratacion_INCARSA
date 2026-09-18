"""correspondencia

Revision ID: 69dabb8fd0ef
Revises: d47ad9c86624
Create Date: 2026-09-08 10:20:07.431382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69dabb8fd0ef'
down_revision: Union[str, Sequence[str], None] = 'd47ad9c86624'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'correspondencia',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('radicado', sa.String(30), nullable=False),
        sa.Column('tipo_correspondencia', sa.VARCHAR(40), nullable=False),
        sa.Column('asunto', sa.VARCHAR(50), nullable=False),        
        sa.Column('procedencia', sa.String(100), nullable=False),
        sa.Column('destino', sa.String(100), nullable=False),
        sa.Column('fecha_envio', sa.DateTime(), server_default=sa.func.now()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
       )
    
    op.execute("""
        INSERT INTO correspondencia (radicado, tipo_correspondencia, asunto, procedencia,destino,fecha_envio) VALUES
        ('RAD-469', '-', '-', '-', '-', NOW())
        ON DUPLICATE KEY UPDATE radicado = VALUES(radicado);
    """)


def downgrade() -> None:
     op.drop_table('correspondencia')
