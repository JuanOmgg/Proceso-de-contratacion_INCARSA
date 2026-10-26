"""add_es_interno_and_fecha_limite_to_formulariogesco

Revision ID: d2e5a1b3c4f7
Revises: c1f4a9b2d8e3
Create Date: 2026-10-23 13:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e5a1b3c4f7'
down_revision: Union[str, Sequence[str], None] = 'c1f4a9b2d8e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    cols_form = [c['name'] for c in insp.get_columns('formularioGesco')]
    if 'es_interno' not in cols_form:
        op.add_column(
            'formularioGesco',
            sa.Column('es_interno', sa.Boolean(), nullable=False, server_default=sa.text('0'))
        )

    if 'fecha_limite' not in cols_form:
        op.add_column(
            'formularioGesco',
            sa.Column('fecha_limite', sa.DateTime(), nullable=True)
        )

    # Si hay formularios con tipo_personal = 'Interno', sincronizar es_interno = 1
    try:
        conn.execute(sa.text("""
            UPDATE formularioGesco
            SET es_interno = 1
            WHERE tipo_personal LIKE '%Interno%'
        """))
    except Exception as e:
        print(f"Aviso actualizando es_interno: {e}")


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    cols_form = [c['name'] for c in insp.get_columns('formularioGesco')]
    if 'fecha_limite' in cols_form:
        op.drop_column('formularioGesco', 'fecha_limite')
    if 'es_interno' in cols_form:
        op.drop_column('formularioGesco', 'es_interno')
