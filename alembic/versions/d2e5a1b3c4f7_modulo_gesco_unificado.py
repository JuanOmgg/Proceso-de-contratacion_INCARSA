"""modulo_gesco_unificado

Revision ID: d2e5a1b3c4f7
Revises: 6eadb14acbdb
Create Date: 2026-10-26 15:00:00.000000

Consolidación unificada del módulo GESCO e Inducciones:
- Tabla formularioGesco con configuración completa (cuotas, creador, modalidad interna, fecha límite).
- Tabla preguntas con metadatos completos (tipo de pregunta, multimedia video/imagen, calificable).
- Tabla opciones_formulario.
- Tabla resultados_formulario con foto de evidencia de la prueba y soporte para personal interno (id_persona nullable).
- Tabla respuestas_usuario_formulario para analítica de aciertos y respuestas por intento.
- Tabla participantes_formulario_interno para captura de datos específicos y foto de participantes internos.
- Actualización de inducciones con vínculo a formulario, responsable y restricción de unicidad compuesta.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e5a1b3c4f7'
down_revision: Union[str, Sequence[str], None] = '6eadb14acbdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    tablas_existentes = insp.get_table_names()

    # =========================================================================
    # 1. TABLA: formularioGesco (Definición completa y unificada)
    # =========================================================================
    if 'formularioGesco' not in tablas_existentes and 'formulariogesco' not in tablas_existentes:
        op.create_table(
            'formularioGesco',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('nombre', sa.String(100), nullable=False),
            sa.Column('descripcion', sa.String(255), nullable=True),
            sa.Column('vigencia', sa.Integer(), nullable=False, server_default='365'),
            sa.Column('tipo_personal', sa.String(150), nullable=False, server_default='TODOS'),
            sa.Column('cantidad_preguntas', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('Tipo_pregunta', sa.String(45), nullable=False, server_default='Multiple choice'),
            sa.Column('config_cuotas', sa.JSON(), nullable=True),
            sa.Column('id_creador', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
            sa.Column('creador_nombre', sa.String(255), nullable=True),
            sa.Column('es_interno', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('fecha_limite', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )
    else:
        # Si ya existe, verificar que contenga todas las columnas unificadas
        nombre_tbl = 'formularioGesco' if 'formularioGesco' in tablas_existentes else 'formulariogesco'
        cols_form = [c['name'] for c in insp.get_columns(nombre_tbl)]
        if 'cantidad_preguntas' not in cols_form:
            op.add_column(nombre_tbl, sa.Column('cantidad_preguntas', sa.Integer(), nullable=False, server_default='1'))
        if 'Tipo_pregunta' not in cols_form:
            op.add_column(nombre_tbl, sa.Column('Tipo_pregunta', sa.String(45), nullable=False, server_default='Multiple choice'))
        if 'config_cuotas' not in cols_form:
            op.add_column(nombre_tbl, sa.Column('config_cuotas', sa.JSON(), nullable=True))
        if 'id_creador' not in cols_form:
            op.add_column(nombre_tbl, sa.Column('id_creador', sa.Integer(), nullable=True))
            try:
                op.create_foreign_key('fk_formulario_creador', nombre_tbl, 'usuarios', ['id_creador'], ['id'], ondelete='SET NULL', onupdate='CASCADE')
            except Exception:
                pass
        if 'creador_nombre' not in cols_form:
            op.add_column(nombre_tbl, sa.Column('creador_nombre', sa.String(255), nullable=True))
        if 'es_interno' not in cols_form:
            op.add_column(nombre_tbl, sa.Column('es_interno', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        if 'fecha_limite' not in cols_form:
            op.add_column(nombre_tbl, sa.Column('fecha_limite', sa.DateTime(), nullable=True))

    # =========================================================================
    # 2. TABLA: preguntas (Definición completa con tipo_pregunta, multimedia y calificación)
    # =========================================================================
    if 'preguntas' not in tablas_existentes:
        op.create_table(
            'preguntas',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('id_formulario', sa.Integer(), sa.ForeignKey('formularioGesco.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('pregunta', sa.String(500), nullable=False),
            sa.Column('tipo_respuesta', sa.String(20), nullable=False),
            sa.Column('tipo_pregunta', sa.String(50), nullable=False, server_default='GENERAL'),
            sa.Column('imagen_url', sa.String(500), nullable=True),
            sa.Column('video_url', sa.String(500), nullable=True),
            sa.Column('es_calificable', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('estado', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )
    else:
        cols_preg = [c['name'] for c in insp.get_columns('preguntas')]
        if 'tipo_pregunta' not in cols_preg:
            op.add_column('preguntas', sa.Column('tipo_pregunta', sa.String(50), nullable=False, server_default='GENERAL'))
        if 'imagen_url' not in cols_preg:
            op.add_column('preguntas', sa.Column('imagen_url', sa.String(500), nullable=True))
        if 'video_url' not in cols_preg:
            op.add_column('preguntas', sa.Column('video_url', sa.String(500), nullable=True))
        if 'es_calificable' not in cols_preg:
            op.add_column('preguntas', sa.Column('es_calificable', sa.Boolean(), nullable=False, server_default='1'))

    # =========================================================================
    # 3. TABLA: opciones_formulario
    # =========================================================================
    if 'opciones_formulario' not in tablas_existentes:
        op.create_table(
            'opciones_formulario',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('id_pregunta', sa.Integer(), sa.ForeignKey('preguntas.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('opcion', sa.String(255), nullable=False),
            sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )

    # =========================================================================
    # 4. TABLA: resultados_formulario (con foto de evidencia y id_persona nullable)
    # =========================================================================
    if 'resultados_formulario' not in tablas_existentes:
        op.create_table(
            'resultados_formulario',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('id_persona', sa.Integer(), sa.ForeignKey('personas.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
            sa.Column('id_formulario', sa.Integer(), sa.ForeignKey('formularioGesco.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('resultado', sa.String(50), nullable=False),
            sa.Column('estado', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('foto_evidencia_url', sa.String(500), nullable=True),
            sa.Column('fecha_realizacion', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )
    else:
        cols_res = [c['name'] for c in insp.get_columns('resultados_formulario')]
        if 'foto_evidencia_url' not in cols_res:
            op.add_column('resultados_formulario', sa.Column('foto_evidencia_url', sa.String(500), nullable=True))
        try:
            op.alter_column('resultados_formulario', 'id_persona', existing_type=sa.Integer(), nullable=True)
        except Exception:
            pass

    # =========================================================================
    # 5. TABLA: respuestas_usuario_formulario (Detalle analítico por respuesta)
    # =========================================================================
    if 'respuestas_usuario_formulario' not in tablas_existentes:
        op.create_table(
            'respuestas_usuario_formulario',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('id_resultado', sa.Integer(), sa.ForeignKey('resultados_formulario.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('id_pregunta', sa.Integer(), sa.ForeignKey('preguntas.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('id_opcion', sa.Integer(), sa.ForeignKey('opciones_formulario.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True),
            sa.Column('texto_respuesta', sa.Text(), nullable=True),
            sa.Column('es_acierto', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('puntos_obtenidos', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )

    # =========================================================================
    # 6. TABLA: participantes_formulario_interno (Personal Interno)
    # =========================================================================
    if 'participantes_formulario_interno' not in tablas_existentes:
        op.create_table(
            'participantes_formulario_interno',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('id_formulario', sa.Integer(), sa.ForeignKey('formularioGesco.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
            sa.Column('id_resultado', sa.Integer(), sa.ForeignKey('resultados_formulario.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True),
            sa.Column('tipo_documento', sa.String(20), nullable=False, server_default='CC'),
            sa.Column('numero_documento', sa.String(50), nullable=False),
            sa.Column('nombres', sa.String(100), nullable=False),
            sa.Column('apellidos', sa.String(100), nullable=True),
            sa.Column('correo', sa.String(255), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Index('idx_part_form', 'id_formulario'),
            sa.Index('idx_part_doc', 'numero_documento'),
            sa.Index('idx_part_resultado', 'id_resultado'),
            mysql_engine='InnoDB',
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )

    # =========================================================================
    # 7. TABLA: inducciones (Vínculo unificado con formularioGesco y responsable)
    # =========================================================================
    if 'inducciones' in tablas_existentes:
        cols_ind = [c['name'] for c in insp.get_columns('inducciones')]
        if 'id_formulario' not in cols_ind:
            op.add_column('inducciones', sa.Column('id_formulario', sa.Integer(), nullable=True))
            try:
                op.create_foreign_key(
                    'fk_inducciones_formulario',
                    'inducciones',
                    'formularioGesco',
                    ['id_formulario'],
                    ['id'],
                    ondelete='CASCADE',
                    onupdate='CASCADE'
                )
            except Exception:
                pass

        if 'responsable' not in cols_ind:
            op.add_column('inducciones', sa.Column('responsable', sa.String(255), nullable=True))

        # Restricción de unicidad compuesta por (id_persona, id_formulario)
        try:
            op.create_index('idx_inducciones_persona', 'inducciones', ['id_persona'], unique=False)
        except Exception:
            pass
        try:
            op.drop_constraint('uq_inducciones_persona', 'inducciones', type_='unique')
        except Exception:
            pass
        try:
            op.create_unique_constraint('uq_persona_formulario', 'inducciones', ['id_persona', 'id_formulario'])
        except Exception:
            pass


def downgrade() -> None:
    # Downgrade estructural inverso
    try:
        op.drop_table('participantes_formulario_interno')
    except Exception:
        pass
    try:
        op.drop_table('respuestas_usuario_formulario')
    except Exception:
        pass
    try:
        op.drop_table('resultados_formulario')
    except Exception:
        pass
    try:
        op.drop_table('opciones_formulario')
    except Exception:
        pass
    try:
        op.drop_table('preguntas')
    except Exception:
        pass
    try:
        op.drop_table('formularioGesco')
    except Exception:
        pass
