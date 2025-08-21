"""Initial schema for RENEC harvester

Revision ID: 001
Revises: 
Create Date: 2025-08-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create EC Standards table
    op.create_table(
        'ec_standards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ec_clave', sa.String(10), nullable=False),
        sa.Column('titulo', sa.Text(), nullable=False),
        sa.Column('version', sa.String(10), nullable=True),
        sa.Column('vigente', sa.Boolean(), default=True),
        sa.Column('sector', sa.String(200), nullable=True),
        sa.Column('sector_id', sa.Integer(), nullable=True),
        sa.Column('comite', sa.String(200), nullable=True),
        sa.Column('comite_id', sa.Integer(), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('competencias', postgresql.JSONB(), nullable=True),
        sa.Column('nivel', sa.String(50), nullable=True),
        sa.Column('duracion_horas', sa.Integer(), nullable=True),
        sa.Column('tipo_norma', sa.String(50), nullable=True),
        sa.Column('fecha_publicacion', sa.Date(), nullable=True),
        sa.Column('fecha_vigencia', sa.Date(), nullable=True),
        sa.Column('perfil_evaluador', sa.Text(), nullable=True),
        sa.Column('criterios_evaluacion', postgresql.JSONB(), nullable=True),
        sa.Column('renec_url', sa.Text(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ec_clave')
    )
    
    # Create indexes for EC Standards
    op.create_index('idx_ec_standards_sector', 'ec_standards', ['sector_id'])
    op.create_index('idx_ec_standards_vigente', 'ec_standards', ['vigente'])
    op.create_index('idx_ec_standards_last_seen', 'ec_standards', ['last_seen'])
    
    # Create Certificadores table
    op.create_table(
        'certificadores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cert_id', sa.String(50), nullable=False),
        sa.Column('tipo', sa.String(3), nullable=False),
        sa.Column('nombre_legal', sa.Text(), nullable=False),
        sa.Column('siglas', sa.String(50), nullable=True),
        sa.Column('estatus', sa.String(20), nullable=True),
        sa.Column('domicilio_texto', sa.Text(), nullable=True),
        sa.Column('estado', sa.String(50), nullable=True),
        sa.Column('estado_inegi', sa.String(2), nullable=True),
        sa.Column('municipio', sa.String(100), nullable=True),
        sa.Column('cp', sa.String(5), nullable=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('correo', sa.String(100), nullable=True),
        sa.Column('sitio_web', sa.String(200), nullable=True),
        sa.Column('representante_legal', sa.String(200), nullable=True),
        sa.Column('fecha_acreditacion', sa.Date(), nullable=True),
        sa.Column('estandares_acreditados', postgresql.JSONB(), nullable=True),
        sa.Column('contactos_adicionales', postgresql.JSONB(), nullable=True),
        sa.Column('src_url', sa.Text(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('row_hash', sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cert_id'),
        sa.CheckConstraint("tipo IN ('ECE', 'OC')", name='check_cert_tipo')
    )
    
    # Create indexes for Certificadores
    op.create_index('idx_certificadores_tipo', 'certificadores', ['tipo'])
    op.create_index('idx_certificadores_estado', 'certificadores', ['estado_inegi'])
    op.create_index('idx_certificadores_estatus', 'certificadores', ['estatus'])
    
    # Create ECE-EC relationship table
    op.create_table(
        'ece_ec',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cert_id', sa.String(50), nullable=False),
        sa.Column('ec_clave', sa.String(10), nullable=False),
        sa.Column('acreditado_desde', sa.Date(), nullable=True),
        sa.Column('run_id', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cert_id'], ['certificadores.cert_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ec_clave'], ['ec_standards.ec_clave'], ondelete='CASCADE'),
        sa.UniqueConstraint('cert_id', 'ec_clave', name='unique_cert_ec')
    )
    
    # Create indexes for relationships
    op.create_index('idx_ece_ec_cert', 'ece_ec', ['cert_id'])
    op.create_index('idx_ece_ec_ec', 'ece_ec', ['ec_clave'])
    
    # Create Sectors table (for Sprint 2)
    op.create_table(
        'sectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sector_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('src_url', sa.Text(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sector_id')
    )
    
    # Create Committees table (for Sprint 2)
    op.create_table(
        'comites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comite_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('sector_id', sa.Integer(), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('src_url', sa.Text(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comite_id'),
        sa.ForeignKeyConstraint(['sector_id'], ['sectors.sector_id'])
    )
    
    # Create Centers table (for Sprint 2)
    op.create_table(
        'centros',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('centro_id', sa.String(50), nullable=False),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('cert_id', sa.String(50), nullable=True),
        sa.Column('domicilio_texto', sa.Text(), nullable=True),
        sa.Column('estado', sa.String(50), nullable=True),
        sa.Column('estado_inegi', sa.String(2), nullable=True),
        sa.Column('municipio', sa.String(100), nullable=True),
        sa.Column('cp', sa.String(5), nullable=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('correo', sa.String(100), nullable=True),
        sa.Column('src_url', sa.Text(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('centro_id'),
        sa.ForeignKeyConstraint(['cert_id'], ['certificadores.cert_id'])
    )
    
    # Create Center-EC relationship table (for Sprint 2)
    op.create_table(
        'centro_ec',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('centro_id', sa.String(50), nullable=False),
        sa.Column('ec_clave', sa.String(10), nullable=False),
        sa.Column('run_id', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['centro_id'], ['centros.centro_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ec_clave'], ['ec_standards.ec_clave'], ondelete='CASCADE'),
        sa.UniqueConstraint('centro_id', 'ec_clave', name='unique_centro_ec')
    )
    
    # Create EC-Sector relationship table
    op.create_table(
        'ec_sector',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ec_clave', sa.String(10), nullable=False),
        sa.Column('sector_id', sa.Integer(), nullable=False),
        sa.Column('comite_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ec_clave'], ['ec_standards.ec_clave'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sector_id'], ['sectors.sector_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['comite_id'], ['comites.comite_id'], ondelete='SET NULL'),
        sa.UniqueConstraint('ec_clave', 'sector_id', name='unique_ec_sector')
    )
    
    # Create harvest runs tracking table
    op.create_table(
        'harvest_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.String(50), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('stats', postgresql.JSONB(), nullable=True),
        sa.Column('errors', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id')
    )
    
    # Create views for current data (latest version of each entity)
    op.execute("""
        CREATE VIEW v_current_ec_standards AS
        SELECT DISTINCT ON (ec_clave) *
        FROM ec_standards
        ORDER BY ec_clave, last_seen DESC;
    """)
    
    op.execute("""
        CREATE VIEW v_current_certificadores AS
        SELECT DISTINCT ON (cert_id) *
        FROM certificadores
        ORDER BY cert_id, last_seen DESC;
    """)
    
    op.execute("""
        CREATE VIEW v_current_centros AS
        SELECT DISTINCT ON (centro_id) *
        FROM centros
        ORDER BY centro_id, last_seen DESC;
    """)


def downgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS v_current_centros")
    op.execute("DROP VIEW IF EXISTS v_current_certificadores")
    op.execute("DROP VIEW IF EXISTS v_current_ec_standards")
    
    # Drop tables in reverse order
    op.drop_table('harvest_runs')
    op.drop_table('ec_sector')
    op.drop_table('centro_ec')
    op.drop_table('centros')
    op.drop_table('comites')
    op.drop_table('sectors')
    op.drop_table('ece_ec')
    op.drop_table('certificadores')
    op.drop_table('ec_standards')