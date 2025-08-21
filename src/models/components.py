"""Component models for RENEC entities."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, 
    String, Text, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.models.base import Base


class TimestampMixin:
    """Mixin for timestamp fields."""
    
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ECStandard(Base, TimestampMixin):
    """EC Standard (Estándar de Competencia) model."""
    
    __tablename__ = "ec_standards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    sector = Column(String(200))
    level = Column(Integer)
    publication_date = Column(DateTime)
    expiration_date = Column(DateTime)
    status = Column(String(50), default="active")
    
    # Content fields
    purpose = Column(Text)
    description = Column(Text)
    occupations = Column(JSON)  # List of related occupations
    
    # Metadata
    url = Column(String(500))
    content_hash = Column(String(64))
    version = Column(Integer, default=1)
    
    # Relationships
    certificadores = relationship(
        "Certificador",
        secondary="certificador_ec_standards",
        back_populates="ec_standards"
    )
    centers = relationship(
        "EvaluationCenter",
        secondary="center_ec_standards",
        back_populates="ec_standards"
    )
    courses = relationship(
        "Course",
        back_populates="ec_standard"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_ec_sector_level", "sector", "level"),
        Index("idx_ec_publication_date", "publication_date"),
        Index("idx_ec_status", "status"),
    )
    
    @validates("code")
    def validate_code(self, key, value):
        """Validate EC code format."""
        if not value or not value.startswith("EC"):
            raise ValueError(f"Invalid EC code format: {value}")
        return value.upper()
    
    def __repr__(self):
        return f"<ECStandard(code={self.code}, title={self.title[:50]}...)>"


class Certificador(Base, TimestampMixin):
    """Certificador (Organismo Certificador) model."""
    
    __tablename__ = "certificadores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    rfc = Column(String(13), index=True)
    
    # Contact information
    contact_name = Column(String(200))
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    website = Column(String(300))
    
    # Address
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100), index=True)
    postal_code = Column(String(10))
    
    # Status
    status = Column(String(50), default="active")
    accreditation_date = Column(DateTime)
    
    # Metadata
    url = Column(String(500))
    content_hash = Column(String(64))
    
    # Relationships
    ec_standards = relationship(
        "ECStandard",
        secondary="certificador_ec_standards",
        back_populates="certificadores"
    )
    evaluation_centers = relationship(
        "EvaluationCenter",
        back_populates="certificador"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_certificador_state_status", "state", "status"),
    )
    
    @validates("code")
    def validate_code(self, key, value):
        """Validate certificador code format."""
        if not value or not value.startswith("OC"):
            raise ValueError(f"Invalid certificador code format: {value}")
        return value.upper()
    
    def __repr__(self):
        return f"<Certificador(code={self.code}, name={self.name[:50]}...)>"


class EvaluationCenter(Base, TimestampMixin):
    """Centro de Evaluación model."""
    
    __tablename__ = "evaluation_centers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    
    # Relationship to certificador
    certificador_id = Column(UUID(as_uuid=True), ForeignKey("certificadores.id"))
    certificador_code = Column(String(20))
    
    # Contact information
    contact_name = Column(String(200))
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    
    # Address
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100), index=True)
    postal_code = Column(String(10))
    
    # Status
    status = Column(String(50), default="active")
    
    # Metadata
    url = Column(String(500))
    content_hash = Column(String(64))
    
    # Relationships
    certificador = relationship("Certificador", back_populates="evaluation_centers")
    ec_standards = relationship(
        "ECStandard",
        secondary="center_ec_standards",
        back_populates="centers"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_center_certificador", "certificador_id"),
        Index("idx_center_state_status", "state", "status"),
    )
    
    @validates("code")
    def validate_code(self, key, value):
        """Validate center code format."""
        if not value or not value.startswith("CE"):
            raise ValueError(f"Invalid center code format: {value}")
        return value.upper()
    
    def __repr__(self):
        return f"<EvaluationCenter(code={self.code}, name={self.name[:50]}...)>"


class Course(Base, TimestampMixin):
    """Course/Training model."""
    
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False)
    
    # EC Standard relationship
    ec_standard_id = Column(UUID(as_uuid=True), ForeignKey("ec_standards.id"))
    ec_code = Column(String(20), index=True)
    
    # Course details
    duration_hours = Column(Integer)
    modality = Column(String(50))  # presencial, en_linea, mixto
    price = Column(Float)
    currency = Column(String(3), default="MXN")
    
    # Schedule
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    schedule = Column(String(200))
    
    # Provider information
    provider_name = Column(String(300))
    provider_type = Column(String(50))  # certificador, center, independent
    
    # Location
    city = Column(String(100))
    state = Column(String(100), index=True)
    
    # Status
    status = Column(String(50), default="active")
    
    # Metadata
    url = Column(String(500))
    content_hash = Column(String(64))
    
    # Relationships
    ec_standard = relationship("ECStandard", back_populates="courses")
    
    # Indexes
    __table_args__ = (
        Index("idx_course_ec_standard", "ec_standard_id"),
        Index("idx_course_dates", "start_date", "end_date"),
        Index("idx_course_state_modality", "state", "modality"),
    )
    
    def __repr__(self):
        return f"<Course(name={self.name[:50]}..., ec_code={self.ec_code})>"