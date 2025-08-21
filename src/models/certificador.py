"""
Certificador model definition.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import Base


class Certificador(Base):
    """Certificador (ECE/OC) model."""
    
    __tablename__ = 'certificadores'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Core fields
    cert_id = Column(String(50), unique=True, nullable=False, index=True)
    tipo = Column(String(3), nullable=False, index=True)
    nombre_legal = Column(Text, nullable=False)
    siglas = Column(String(50))
    estatus = Column(String(20), index=True)
    
    # Location
    domicilio_texto = Column(Text)
    estado = Column(String(50))
    estado_inegi = Column(String(2), index=True)
    municipio = Column(String(100))
    cp = Column(String(5))
    
    # Contact
    telefono = Column(String(20))
    correo = Column(String(100))
    sitio_web = Column(String(200))
    representante_legal = Column(String(200))
    
    # Accreditation
    fecha_acreditacion = Column(Date)
    estandares_acreditados = Column(JSONB)
    contactos_adicionales = Column(JSONB)
    
    # Source
    src_url = Column(Text, nullable=False)
    
    # Temporal tracking
    first_seen = Column(DateTime, server_default=func.now(), nullable=False)
    last_seen = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Change detection
    row_hash = Column(String(64))
    
    # Constraints
    __table_args__ = (
        CheckConstraint("tipo IN ('ECE', 'OC')", name='check_cert_tipo'),
    )
    
    def __repr__(self):
        return f"<Certificador(cert_id='{self.cert_id}', tipo='{self.tipo}', nombre='{self.nombre_legal[:50]}...')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'cert_id': self.cert_id,
            'tipo': self.tipo,
            'nombre_legal': self.nombre_legal,
            'siglas': self.siglas,
            'estatus': self.estatus,
            'domicilio_texto': self.domicilio_texto,
            'estado': self.estado,
            'estado_inegi': self.estado_inegi,
            'municipio': self.municipio,
            'cp': self.cp,
            'telefono': self.telefono,
            'correo': self.correo,
            'sitio_web': self.sitio_web,
            'representante_legal': self.representante_legal,
            'fecha_acreditacion': self.fecha_acreditacion.isoformat() if self.fecha_acreditacion else None,
            'estandares_acreditados': self.estandares_acreditados,
            'contactos_adicionales': self.contactos_adicionales,
            'src_url': self.src_url,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'row_hash': self.row_hash
        }