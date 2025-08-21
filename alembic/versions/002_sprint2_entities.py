"""Sprint 2 entities and relationships

Revision ID: 002
Revises: 001
Create Date: 2025-08-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create ec_standards_v2 table
    op.create_table('ec_standards_v2',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ec_clave', sa.String(length=10), nullable=False),
        sa.Column('titulo', sa.Text(), nullable=False),
        sa.Column('version', sa.String(length=10), nullable=True),
        sa.Column('vigente', sa.Boolean(), nullable=True),
        sa.Column('sector', sa.String(length=200), nullable=True),
        sa.Column('sector_id', sa.Integer(), nullable=True),
        sa.Column('comite', sa.String(length=200), nullable=True),
        sa.Column('comite_id', sa.Integer(), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('competencias', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('nivel', sa.String(length=50), nullable=True),
        sa.Column('duracion_horas', sa.Integer(), nullable=True),
        sa.Column('tipo_norma', sa.String(length=50), nullable=True),
        sa.Column('fecha_publicacion', sa.Date(), nullable=True),
        sa.Column('fecha_vigencia', sa.Date(), nullable=True),
        sa.Column('perfil_evaluador', sa.Text(), nullable=True),
        sa.Column('criterios_evaluacion', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('renec_url', sa.String(length=500), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ec_clave')
    )
    op.create_index(op.f('ix_ec_standards_v2_ec_clave'), 'ec_standards_v2', ['ec_clave'], unique=False)
    op.create_index(op.f('ix_ec_standards_v2_sector_id'), 'ec_standards_v2', ['sector_id'], unique=False)
    op.create_index(op.f('ix_ec_standards_v2_vigente'), 'ec_standards_v2', ['vigente'], unique=False)

    # Create certificadores_v2 table
    op.create_table('certificadores_v2',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cert_id', sa.String(length=50), nullable=False),
        sa.Column('tipo', sa.String(length=3), nullable=False),
        sa.Column('nombre_legal', sa.Text(), nullable=False),
        sa.Column('siglas', sa.String(length=50), nullable=True),
        sa.Column('estatus', sa.String(length=20), nullable=True),
        sa.Column('domicilio_texto', sa.Text(), nullable=True),
        sa.Column('estado', sa.String(length=100), nullable=True),
        sa.Column('estado_inegi', sa.String(length=2), nullable=True),
        sa.Column('municipio', sa.String(length=200), nullable=True),
        sa.Column('cp', sa.String(length=10), nullable=True),
        sa.Column('telefono', sa.String(length=100), nullable=True),
        sa.Column('correo', sa.String(length=200), nullable=True),
        sa.Column('sitio_web', sa.String(length=500), nullable=True),
        sa.Column('representante_legal', sa.String(length=200), nullable=True),
        sa.Column('fecha_acreditacion', sa.Date(), nullable=True),
        sa.Column('estandares_acreditados', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('contactos_adicionales', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('src_url', sa.String(length=500), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("tipo IN ('ECE', 'OC')", name='check_tipo_valid'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cert_id')
    )
    op.create_index(op.f('ix_certificadores_v2_cert_id'), 'certificadores_v2', ['cert_id'], unique=False)
    op.create_index(op.f('ix_certificadores_v2_estado_inegi'), 'certificadores_v2', ['estado_inegi'], unique=False)
    op.create_index(op.f('ix_certificadores_v2_estatus'), 'certificadores_v2', ['estatus'], unique=False)
    op.create_index(op.f('ix_certificadores_v2_tipo'), 'certificadores_v2', ['tipo'], unique=False)

    # Create sectores table
    op.create_table('sectores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sector_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('src_url', sa.String(length=500), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sector_id')
    )
    op.create_index(op.f('ix_sectores_sector_id'), 'sectores', ['sector_id'], unique=False)

    # Create comites table
    op.create_table('comites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comite_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=300), nullable=False),
        sa.Column('sector_id', sa.Integer(), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('institucion_representada', sa.String(length=300), nullable=True),
        sa.Column('src_url', sa.String(length=500), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sector_id'], ['sectores.sector_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comite_id')
    )
    op.create_index(op.f('ix_comites_comite_id'), 'comites', ['comite_id'], unique=False)
    op.create_index(op.f('ix_comites_sector_id'), 'comites', ['sector_id'], unique=False)

    # Create centros table
    op.create_table('centros',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('centro_id', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=300), nullable=False),
        sa.Column('estado', sa.String(length=100), nullable=True),
        sa.Column('estado_inegi', sa.String(length=2), nullable=True),
        sa.Column('municipio', sa.String(length=200), nullable=True),
        sa.Column('domicilio', sa.Text(), nullable=True),
        sa.Column('telefono', sa.String(length=100), nullable=True),
        sa.Column('extension', sa.String(length=20), nullable=True),
        sa.Column('correo', sa.String(length=200), nullable=True),
        sa.Column('sitio_web', sa.String(length=500), nullable=True),
        sa.Column('coordinador', sa.String(length=200), nullable=True),
        sa.Column('certificador_id', sa.String(length=50), nullable=True),
        sa.Column('src_url', sa.String(length=500), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['certificador_id'], ['certificadores_v2.cert_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('centro_id')
    )
    op.create_index(op.f('ix_centros_centro_id'), 'centros', ['centro_id'], unique=False)
    op.create_index(op.f('ix_centros_certificador_id'), 'centros', ['certificador_id'], unique=False)
    op.create_index(op.f('ix_centros_estado_inegi'), 'centros', ['estado_inegi'], unique=False)

    # Create ece_ec relationship table
    op.create_table('ece_ec',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cert_id', sa.String(length=50), nullable=False),
        sa.Column('ec_clave', sa.String(length=10), nullable=False),
        sa.Column('acreditado_desde', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cert_id'], ['certificadores_v2.cert_id'], ),
        sa.ForeignKeyConstraint(['ec_clave'], ['ec_standards_v2.ec_clave'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cert_id', 'ec_clave', name='uq_ece_ec_cert_ec')
    )
    op.create_index(op.f('ix_ece_ec_cert_id'), 'ece_ec', ['cert_id'], unique=False)
    op.create_index(op.f('ix_ece_ec_ec_clave'), 'ece_ec', ['ec_clave'], unique=False)

    # Create centro_ec relationship table
    op.create_table('centro_ec',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('centro_id', sa.String(length=50), nullable=False),
        sa.Column('ec_clave', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['centro_id'], ['centros.centro_id'], ),
        sa.ForeignKeyConstraint(['ec_clave'], ['ec_standards_v2.ec_clave'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('centro_id', 'ec_clave', name='uq_centro_ec_centro_ec')
    )
    op.create_index(op.f('ix_centro_ec_centro_id'), 'centro_ec', ['centro_id'], unique=False)
    op.create_index(op.f('ix_centro_ec_ec_clave'), 'centro_ec', ['ec_clave'], unique=False)

    # Create ec_sector relationship table
    op.create_table('ec_sector',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ec_clave', sa.String(length=10), nullable=False),
        sa.Column('sector_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ec_clave'], ['ec_standards_v2.ec_clave'], ),
        sa.ForeignKeyConstraint(['sector_id'], ['sectores.sector_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ec_clave', 'sector_id', name='uq_ec_sector_ec_sector')
    )
    op.create_index(op.f('ix_ec_sector_ec_clave'), 'ec_sector', ['ec_clave'], unique=False)
    op.create_index(op.f('ix_ec_sector_sector_id'), 'ec_sector', ['sector_id'], unique=False)

    # Create harvest_runs table
    op.create_table('harvest_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('harvest_id', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('mode', sa.String(length=20), nullable=False),
        sa.Column('spider_name', sa.String(length=50), nullable=False),
        sa.Column('items_scraped', sa.Integer(), nullable=True),
        sa.Column('pages_crawled', sa.Integer(), nullable=True),
        sa.Column('errors', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('log_file', sa.String(length=500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('harvest_id')
    )
    op.create_index(op.f('ix_harvest_runs_harvest_id'), 'harvest_runs', ['harvest_id'], unique=False)
    op.create_index(op.f('ix_harvest_runs_start_time'), 'harvest_runs', ['start_time'], unique=False)
    op.create_index(op.f('ix_harvest_runs_status'), 'harvest_runs', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_harvest_runs_status'), table_name='harvest_runs')
    op.drop_index(op.f('ix_harvest_runs_start_time'), table_name='harvest_runs')
    op.drop_index(op.f('ix_harvest_runs_harvest_id'), table_name='harvest_runs')
    op.drop_table('harvest_runs')
    op.drop_index(op.f('ix_ec_sector_sector_id'), table_name='ec_sector')
    op.drop_index(op.f('ix_ec_sector_ec_clave'), table_name='ec_sector')
    op.drop_table('ec_sector')
    op.drop_index(op.f('ix_centro_ec_ec_clave'), table_name='centro_ec')
    op.drop_index(op.f('ix_centro_ec_centro_id'), table_name='centro_ec')
    op.drop_table('centro_ec')
    op.drop_index(op.f('ix_ece_ec_ec_clave'), table_name='ece_ec')
    op.drop_index(op.f('ix_ece_ec_cert_id'), table_name='ece_ec')
    op.drop_table('ece_ec')
    op.drop_index(op.f('ix_centros_estado_inegi'), table_name='centros')
    op.drop_index(op.f('ix_centros_certificador_id'), table_name='centros')
    op.drop_index(op.f('ix_centros_centro_id'), table_name='centros')
    op.drop_table('centros')
    op.drop_index(op.f('ix_comites_sector_id'), table_name='comites')
    op.drop_index(op.f('ix_comites_comite_id'), table_name='comites')
    op.drop_table('comites')
    op.drop_index(op.f('ix_sectores_sector_id'), table_name='sectores')
    op.drop_table('sectores')
    op.drop_index(op.f('ix_certificadores_v2_tipo'), table_name='certificadores_v2')
    op.drop_index(op.f('ix_certificadores_v2_estatus'), table_name='certificadores_v2')
    op.drop_index(op.f('ix_certificadores_v2_estado_inegi'), table_name='certificadores_v2')
    op.drop_index(op.f('ix_certificadores_v2_cert_id'), table_name='certificadores_v2')
    op.drop_table('certificadores_v2')
    op.drop_index(op.f('ix_ec_standards_v2_vigente'), table_name='ec_standards_v2')
    op.drop_index(op.f('ix_ec_standards_v2_sector_id'), table_name='ec_standards_v2')
    op.drop_index(op.f('ix_ec_standards_v2_ec_clave'), table_name='ec_standards_v2')
    op.drop_table('ec_standards_v2')