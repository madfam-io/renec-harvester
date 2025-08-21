"""
Sector model definition.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.sql import func

from .base import Base


class Sector(Base):
    """Sector productivo model."""
    
    __tablename__ = 'sectors'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Core fields
    sector_id = Column(Integer, unique=True, nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    
    # Statistics
    num_comites = Column(Integer)
    num_estandares = Column(Integer)
    
    # Dates
    fecha_creacion = Column(Date)
    
    # Source
    src_url = Column(Text, nullable=False)
    
    # Temporal tracking
    first_seen = Column(DateTime, server_default=func.now(), nullable=False)
    last_seen = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Sector(sector_id={self.sector_id}, nombre='{self.nombre[:50]}...')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'sector_id': self.sector_id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'num_comites': self.num_comites,
            'num_estandares': self.num_estandares,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'src_url': self.src_url,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }