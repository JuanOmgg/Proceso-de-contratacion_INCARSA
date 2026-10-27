"""formularioGesco y actualizacion de inducciones

Revision ID: 28e20c185481
Revises: 6eadb14acbdb
Create Date: 2026-10-13 10:11:00.020177

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28e20c185481'
down_revision: Union[str, Sequence[str], None] = '6eadb14acbdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Crear tabla formularioGesco
    op.create_table(
        'formularioGesco',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.String(255), nullable=True),
        sa.Column('vigencia', sa.Integer(), nullable=False, server_default='365'),
        sa.Column('tipo_personal', sa.String(150), nullable=False, server_default='TODOS'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now(), nullable=True),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # 2. Agregar id_formulario a inducciones
    op.add_column(
        'inducciones',
        sa.Column('id_formulario', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_inducciones_formulario',
        'inducciones',
        'formularioGesco',
        ['id_formulario'],
        ['id'],
        ondelete='CASCADE',
        onupdate='CASCADE'
    )
    # 3. Asegurar índice en id_persona para FK personas, retirar unicidad simple y agregar unicidad compuesta
    op.create_index('idx_inducciones_persona', 'inducciones', ['id_persona'], unique=False)
    op.drop_constraint('uq_inducciones_persona', 'inducciones', type_='unique')
    op.create_unique_constraint('uq_persona_formulario', 'inducciones', ['id_persona', 'id_formulario'])


def downgrade() -> None:
    op.drop_constraint('uq_persona_formulario', 'inducciones', type_='unique')
    op.create_unique_constraint('uq_inducciones_persona', 'inducciones', ['id_persona'])
    op.drop_index('idx_inducciones_persona', 'inducciones')
    op.drop_constraint('fk_inducciones_formulario', 'inducciones', type_='foreignkey')
    op.drop_column('inducciones', 'id_formulario')
    op.drop_table('formularioGesco')
