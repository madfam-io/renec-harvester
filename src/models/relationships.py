"""Relationship tables for many-to-many associations."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base


# Association table for Certificador <-> EC Standard
certificador_ec_standards = Table(
    "certificador_ec_standards",
    Base.metadata,
    Column("certificador_id", UUID(as_uuid=True), ForeignKey("certificadores.id"), primary_key=True),
    Column("ec_standard_id", UUID(as_uuid=True), ForeignKey("ec_standards.id"), primary_key=True),
    Column("relationship_type", String(50), default="certifies"),
    Column("created_at", DateTime, default=datetime.utcnow),
    UniqueConstraint("certificador_id", "ec_standard_id", name="uq_certificador_ec"),
)

# Association table for Center <-> EC Standard
center_ec_standards = Table(
    "center_ec_standards",
    Base.metadata,
    Column("center_id", UUID(as_uuid=True), ForeignKey("evaluation_centers.id"), primary_key=True),
    Column("ec_standard_id", UUID(as_uuid=True), ForeignKey("ec_standards.id"), primary_key=True),
    Column("relationship_type", String(50), default="evaluates"),
    Column("created_at", DateTime, default=datetime.utcnow),
    UniqueConstraint("center_id", "ec_standard_id", name="uq_center_ec"),
)

# Export association tables as classes for easier access
CertificadorECStandard = certificador_ec_standards
CenterECStandard = center_ec_standards
CourseECStandard = None  # Direct foreign key relationship, not many-to-many