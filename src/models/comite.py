"""
Comité model definition.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import Base


class Comite(Base):
    """Comité de Gestión por Competencias model."""
    
    __tablename__ = 'comites'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Core fields
    comite_id = Column(Integer, unique=True, nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    sector_id = Column(Integer, ForeignKey('sectors.sector_id'))
    
    # Details
    descripcion = Column(Text)
    objetivo = Column(Text)
    num_estandares = Column(Integer)
    
    # Contact
    contacto = Column(JSONB)  # Dict with email, phone, etc.
    
    # Dates
    fecha_creacion = Column(Date)
    fecha_actualizacion = Column(Date)
    
    # EC Standards (list of codes)
    estandares = Column(JSONB)
    
    # Source
    src_url = Column(Text, nullable=False)
    
    # Temporal tracking
    first_seen = Column(DateTime, server_default=func.now(), nullable=False)
    last_seen = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Comite(comite_id={self.comite_id}, nombre='{self.nombre[:50]}...')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'comite_id': self.comite_id,
            'nombre': self.nombre,
            'sector_id': self.sector_id,
            'descripcion': self.descripcion,
            'objetivo': self.objetivo,
            'num_estandares': self.num_estandares,
            'contacto': self.contacto,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'estandares': self.estandares,
            'src_url': self.src_url,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }