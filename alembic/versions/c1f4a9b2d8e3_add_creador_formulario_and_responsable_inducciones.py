"""add_creador_formulario_and_responsable_inducciones

Revision ID: c1f4a9b2d8e3
Revises: 8a96c8185468
Create Date: 2026-10-23 09:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1f4a9b2d8e3'
down_revision: Union[str, Sequence[str], None] = '8a96c8185468'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # 1. Columnas en formularioGesco
    cols_form = [c['name'] for c in insp.get_columns('formularioGesco')]
    if 'id_creador' not in cols_form:
        op.add_column(
            'formularioGesco',
            sa.Column('id_creador', sa.Integer(), nullable=True)
        )
        try:
            op.create_foreign_key(
                'fk_formulario_creador',
                'formularioGesco',
                'usuarios',
                ['id_creador'],
                ['id'],
                ondelete='SET NULL',
                onupdate='CASCADE'
            )
        except Exception:
            pass

    if 'creador_nombre' not in cols_form:
        op.add_column(
            'formularioGesco',
            sa.Column('creador_nombre', sa.String(255), nullable=True)
        )

    # 2. Columna responsable en inducciones
    cols_ind = [c['name'] for c in insp.get_columns('inducciones')]
    if 'responsable' not in cols_ind:
        op.add_column(
            'inducciones',
            sa.Column('responsable', sa.String(255), nullable=True)
        )

    # 3. Poblar datos existentes
    try:
        # Asignar creador por defecto para formularios existentes que tengan NULL
        conn.execute(sa.text("""
            UPDATE formularioGesco fg
            JOIN (
                SELECT id, CONCAT(nombres, ' ', COALESCE(apellidos, '')) AS nom
                FROM usuarios
                ORDER BY id ASC LIMIT 1
            ) u
            SET fg.id_creador = u.id,
                fg.creador_nombre = TRIM(u.nom)
            WHERE fg.id_creador IS NULL OR fg.creador_nombre IS NULL
        """))

        # Asignar el creador del formulario como responsable de inducciones existentes
        conn.execute(sa.text("""
            UPDATE inducciones ind
            JOIN formularioGesco fg ON ind.id_formulario = fg.id
            SET ind.responsable = fg.creador_nombre
            WHERE ind.responsable IS NULL AND fg.creador_nombre IS NOT NULL
        """))
    except Exception as e:
        print(f"Aviso actualizando datos existentes: {e}")


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    cols_ind = [c['name'] for c in insp.get_columns('inducciones')]
    if 'responsable' in cols_ind:
        op.drop_column('inducciones', 'responsable')

    cols_form = [c['name'] for c in insp.get_columns('formularioGesco')]
    if 'creador_nombre' in cols_form:
        op.drop_column('formularioGesco', 'creador_nombre')
    if 'id_creador' in cols_form:
        try:
            op.drop_constraint('fk_formulario_creador', 'formularioGesco', type_='foreignkey')
        except Exception:
            pass
        op.drop_column('formularioGesco', 'id_creador')
