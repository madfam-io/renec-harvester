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
    
    __tablename__ = 'centros'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Core fields
    centro_id = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    cert_id = Column(String(50), ForeignKey('certificadores.cert_id'))
    
    # Location
    domicilio_texto = Column(Text)
    estado = Column(String(50))
    estado_inegi = Column(String(2), index=True)
    municipio = Column(String(100))
    cp = Column(String(5))
    
    # Contact
    telefono = Column(String(20))
    correo = Column(String(100))
    responsable = Column(String(200))
    
    # Details
    fecha_acreditacion = Column(Date)
    modalidades = Column(JSONB)  # List of evaluation modalities
    estandares_evaluacion = Column(JSONB)  # List of EC codes
    
    # Source
    src_url = Column(Text, nullable=False)
    
    # Temporal tracking
    first_seen = Column(DateTime, server_default=func.now(), nullable=False)
    last_seen = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Change detection
    row_hash = Column(String(64))
    
    def __repr__(self):
        return f"<Centro(centro_id='{self.centro_id}', nombre='{self.nombre[:50]}...')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'centro_id': self.centro_id,
            'nombre': self.nombre,
            'cert_id': self.cert_id,
            'domicilio_texto': self.domicilio_texto,
            'estado': self.estado,
            'estado_inegi': self.estado_inegi,
            'municipio': self.municipio,
            'cp': self.cp,
            'telefono': self.telefono,
            'correo': self.correo,
            'responsable': self.responsable,
            'fecha_acreditacion': self.fecha_acreditacion.isoformat() if self.fecha_acreditacion else None,
            'modalidades': self.modalidades,
            'estandares_evaluacion': self.estandares_evaluacion,
            'src_url': self.src_url,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'row_hash': self.row_hash
        }