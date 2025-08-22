"""
Centro (Evaluation Center) model definition.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import Base


class Centro(Base):
    """Centro de Evaluación model."""
    
    __tablename__ = 'centros_v2'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Core fields
    centro_id = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(300), nullable=False)
    certificador_id = Column(String(50), ForeignKey('certificadores_v2.cert_id'))
    
    # Location
    estado = Column(String(100))
    estado_inegi = Column(String(2), index=True)
    municipio = Column(String(200))
    domicilio = Column(Text)
    
    # Contact
    telefono = Column(String(100))
    extension = Column(String(20))
    correo = Column(String(200))
    sitio_web = Column(String(500))
    coordinador = Column(String(200))
    
    # Source and metadata
    src_url = Column(String(500))
    content_hash = Column(String(64))
    
    # Temporal tracking
    first_seen = Column(DateTime, server_default=func.now(), nullable=False)
    last_seen = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Centro(centro_id='{self.centro_id}', nombre='{self.nombre[:50]}...')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'centro_id': self.centro_id,
            'nombre': self.nombre,
            'certificador_id': self.certificador_id,
            'domicilio': self.domicilio,
            'estado': self.estado,
            'estado_inegi': self.estado_inegi,
            'municipio': self.municipio,
            'telefono': self.telefono,
            'extension': self.extension,
            'correo': self.correo,
            'sitio_web': self.sitio_web,
            'coordinador': self.coordinador,
            'src_url': self.src_url,
            'content_hash': self.content_hash,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }