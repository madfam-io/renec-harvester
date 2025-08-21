"""
EC Standard model definition.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import Base


class ECStandard(Base):
    """EC Standard (Estándar de Competencia) model."""
    
    __tablename__ = 'ec_standards_v2'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Core fields
    ec_clave = Column(String(10), unique=True, nullable=False, index=True)
    titulo = Column(Text, nullable=False)
    version = Column(String(10))
    vigente = Column(Boolean, default=True, index=True)
    
    # Sector and committee
    sector = Column(String(200))
    sector_id = Column(Integer, index=True)
    comite = Column(String(200))
    comite_id = Column(Integer)
    
    # Details
    descripcion = Column(Text)
    competencias = Column(JSONB)
    nivel = Column(String(50))
    duracion_horas = Column(Integer)
    tipo_norma = Column(String(50))
    
    # Dates
    fecha_publicacion = Column(Date)
    fecha_vigencia = Column(Date)
    
    # Evaluation
    perfil_evaluador = Column(Text)
    criterios_evaluacion = Column(JSONB)
    
    # Source
    renec_url = Column(Text, nullable=False)
    
    # Temporal tracking
    first_seen = Column(DateTime, server_default=func.now(), nullable=False)
    last_seen = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Change detection
    content_hash = Column(String(64))
    
    def __repr__(self):
        return f"<ECStandard(ec_clave='{self.ec_clave}', titulo='{self.titulo[:50]}...')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'ec_clave': self.ec_clave,
            'titulo': self.titulo,
            'version': self.version,
            'vigente': self.vigente,
            'sector': self.sector,
            'sector_id': self.sector_id,
            'comite': self.comite,
            'comite_id': self.comite_id,
            'descripcion': self.descripcion,
            'competencias': self.competencias,
            'nivel': self.nivel,
            'duracion_horas': self.duracion_horas,
            'tipo_norma': self.tipo_norma,
            'fecha_publicacion': self.fecha_publicacion.isoformat() if self.fecha_publicacion else None,
            'fecha_vigencia': self.fecha_vigencia.isoformat() if self.fecha_vigencia else None,
            'perfil_evaluador': self.perfil_evaluador,
            'criterios_evaluacion': self.criterios_evaluacion,
            'renec_url': self.renec_url,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'content_hash': self.content_hash
        }