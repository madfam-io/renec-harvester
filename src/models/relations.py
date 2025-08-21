"""
Relationship models for RENEC entities.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import Base


class ECEEC(Base):
    """ECE-EC Standard relationship."""
    
    __tablename__ = 'ece_ec'
    
    id = Column(Integer, primary_key=True)
    cert_id = Column(String(50), ForeignKey('certificadores.cert_id', ondelete='CASCADE'), nullable=False)
    ec_clave = Column(String(10), ForeignKey('ec_standards.ec_clave', ondelete='CASCADE'), nullable=False)
    acreditado_desde = Column(Date)
    run_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('cert_id', 'ec_clave', name='unique_cert_ec'),
    )
    
    def __repr__(self):
        return f"<ECEEC(cert_id='{self.cert_id}', ec_clave='{self.ec_clave}')>"


class CentroEC(Base):
    """Centro-EC Standard relationship."""
    
    __tablename__ = 'centro_ec'
    
    id = Column(Integer, primary_key=True)
    centro_id = Column(String(50), ForeignKey('centros.centro_id', ondelete='CASCADE'), nullable=False)
    ec_clave = Column(String(10), ForeignKey('ec_standards.ec_clave', ondelete='CASCADE'), nullable=False)
    run_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('centro_id', 'ec_clave', name='unique_centro_ec'),
    )
    
    def __repr__(self):
        return f"<CentroEC(centro_id='{self.centro_id}', ec_clave='{self.ec_clave}')>"


class ECSector(Base):
    """EC Standard-Sector relationship."""
    
    __tablename__ = 'ec_sector'
    
    id = Column(Integer, primary_key=True)
    ec_clave = Column(String(10), ForeignKey('ec_standards.ec_clave', ondelete='CASCADE'), nullable=False)
    sector_id = Column(Integer, ForeignKey('sectors.sector_id', ondelete='CASCADE'), nullable=False)
    comite_id = Column(Integer, ForeignKey('comites.comite_id', ondelete='SET NULL'))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('ec_clave', 'sector_id', name='unique_ec_sector'),
    )
    
    def __repr__(self):
        return f"<ECSector(ec_clave='{self.ec_clave}', sector_id={self.sector_id})>"


class HarvestRun(Base):
    """Harvest run tracking."""
    
    __tablename__ = 'harvest_runs'
    
    id = Column(Integer, primary_key=True)
    run_id = Column(String(50), unique=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String(20), nullable=False)  # running, completed, failed
    stats = Column(JSONB)  # Statistics about the run
    errors = Column(JSONB)  # Any errors encountered
    
    def __repr__(self):
        return f"<HarvestRun(run_id='{self.run_id}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'run_id': self.run_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'stats': self.stats,
            'errors': self.errors
        }