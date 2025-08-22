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
    cert_id = Column(String(50), ForeignKey('certificadores_v2.cert_id', ondelete='CASCADE'), nullable=False)
    ec_clave = Column(String(10), ForeignKey('ec_standards_v2.ec_clave', ondelete='CASCADE'), nullable=False)
    acreditado_desde = Column(Date)
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
    centro_id = Column(String(50), ForeignKey('centros_v2.centro_id', ondelete='CASCADE'), nullable=False)
    ec_clave = Column(String(10), ForeignKey('ec_standards_v2.ec_clave', ondelete='CASCADE'), nullable=False)
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
    ec_clave = Column(String(10), ForeignKey('ec_standards_v2.ec_clave', ondelete='CASCADE'), nullable=False)
    sector_id = Column(Integer, ForeignKey('sectors.sector_id', ondelete='CASCADE'), nullable=False)
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
    harvest_id = Column(String(50), unique=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    mode = Column(String(20), nullable=False)
    spider_name = Column(String(50), nullable=False)
    items_scraped = Column(Integer)
    pages_crawled = Column(Integer)
    errors = Column(Integer)
    status = Column(String(20), nullable=False)
    log_file = Column(String(500))
    run_metadata = Column('metadata', JSONB)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<HarvestRun(harvest_id='{self.harvest_id}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'harvest_id': self.harvest_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'mode': self.mode,
            'spider_name': self.spider_name,
            'items_scraped': self.items_scraped,
            'pages_crawled': self.pages_crawled,
            'errors': self.errors,
            'status': self.status,
            'log_file': self.log_file,
            'metadata': self.run_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }