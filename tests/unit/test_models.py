"""Unit tests for database models."""

import pytest
from datetime import datetime
from uuid import UUID

from src.models.components import ECStandard, Certificador, EvaluationCenter, Course
from src.models.relationships import certificador_ec_standards, center_ec_standards


class TestECStandard:
    """Test cases for ECStandard model."""
    
    def test_create_ec_standard(self, db_session):
        """Test creating an EC standard."""
        ec = ECStandard(
            code="EC0001",
            title="Competencia en desarrollo de software",
            sector="Tecnología",
            level=3,
            publication_date=datetime(2023, 1, 15),
            status="active",
        )
        
        db_session.add(ec)
        db_session.commit()
        
        # Verify
        saved_ec = db_session.query(ECStandard).filter_by(code="EC0001").first()
        assert saved_ec is not None
        assert saved_ec.title == "Competencia en desarrollo de software"
        assert saved_ec.sector == "Tecnología"
        assert saved_ec.level == 3
        assert isinstance(saved_ec.id, UUID)
    
    def test_ec_standard_code_validation(self, db_session):
        """Test EC standard code validation."""
        # Valid code
        ec = ECStandard(code="EC1234", title="Test")
        assert ec.code == "EC1234"
        
        # Invalid code should raise error
        with pytest.raises(ValueError, match="Invalid EC code format"):
            ECStandard(code="INVALID", title="Test")
        
        # Code should be uppercase
        ec2 = ECStandard(code="ec5678", title="Test")
        assert ec2.code == "EC5678"
    
    def test_ec_standard_relationships(self, db_session):
        """Test EC standard relationships."""
        # Create EC standard
        ec = ECStandard(code="EC0001", title="Test EC")
        db_session.add(ec)
        
        # Create certificador
        cert = Certificador(code="OC001", name="Test Cert")
        db_session.add(cert)
        
        db_session.commit()
        
        # Add relationship
        db_session.execute(
            certificador_ec_standards.insert().values(
                certificador_id=cert.id,
                ec_standard_id=ec.id,
            )
        )
        db_session.commit()
        
        # Verify relationship
        ec_refreshed = db_session.query(ECStandard).filter_by(code="EC0001").first()
        assert len(ec_refreshed.certificadores) == 1
        assert ec_refreshed.certificadores[0].code == "OC001"


class TestCertificador:
    """Test cases for Certificador model."""
    
    def test_create_certificador(self, db_session):
        """Test creating a certificador."""
        cert = Certificador(
            code="OC001",
            name="Centro de Certificación Tecnológica",
            rfc="CCT123456ABC",
            contact_email="contacto@certificador.mx",
            contact_phone="+525555555555",
            state="Ciudad de México",
            status="active",
        )
        
        db_session.add(cert)
        db_session.commit()
        
        # Verify
        saved_cert = db_session.query(Certificador).filter_by(code="OC001").first()
        assert saved_cert is not None
        assert saved_cert.name == "Centro de Certificación Tecnológica"
        assert saved_cert.rfc == "CCT123456ABC"
    
    def test_certificador_code_validation(self):
        """Test certificador code validation."""
        # Valid code
        cert = Certificador(code="OC123", name="Test")
        assert cert.code == "OC123"
        
        # Invalid code
        with pytest.raises(ValueError, match="Invalid certificador code format"):
            Certificador(code="INVALID", name="Test")
    
    def test_certificador_evaluation_centers(self, db_session):
        """Test certificador-center relationship."""
        # Create certificador
        cert = Certificador(code="OC001", name="Test Cert")
        db_session.add(cert)
        db_session.commit()
        
        # Create evaluation center
        center = EvaluationCenter(
            code="CE00001",
            name="Test Center",
            certificador_id=cert.id,
            certificador_code="OC001",
        )
        db_session.add(center)
        db_session.commit()
        
        # Verify relationship
        cert_refreshed = db_session.query(Certificador).filter_by(code="OC001").first()
        assert len(cert_refreshed.evaluation_centers) == 1
        assert cert_refreshed.evaluation_centers[0].code == "CE00001"


class TestEvaluationCenter:
    """Test cases for EvaluationCenter model."""
    
    def test_create_evaluation_center(self, db_session):
        """Test creating an evaluation center."""
        center = EvaluationCenter(
            code="CE00001",
            name="Centro de Evaluación Norte",
            certificador_code="OC001",
            contact_email="centro@evaluacion.mx",
            state="Nuevo León",
            status="active",
        )
        
        db_session.add(center)
        db_session.commit()
        
        # Verify
        saved_center = db_session.query(EvaluationCenter).filter_by(code="CE00001").first()
        assert saved_center is not None
        assert saved_center.name == "Centro de Evaluación Norte"
        assert saved_center.certificador_code == "OC001"
    
    def test_center_code_validation(self):
        """Test center code validation."""
        # Valid code
        center = EvaluationCenter(code="CE12345", name="Test")
        assert center.code == "CE12345"
        
        # Invalid code
        with pytest.raises(ValueError, match="Invalid center code format"):
            EvaluationCenter(code="INVALID", name="Test")


class TestCourse:
    """Test cases for Course model."""
    
    def test_create_course(self, db_session):
        """Test creating a course."""
        course = Course(
            name="Curso de preparación EC0001",
            ec_code="EC0001",
            duration_hours=40,
            modality="presencial",
            start_date=datetime(2024, 1, 15),
            provider_name="Instituto de Capacitación",
            state="Jalisco",
        )
        
        db_session.add(course)
        db_session.commit()
        
        # Verify
        saved_course = db_session.query(Course).filter_by(name="Curso de preparación EC0001").first()
        assert saved_course is not None
        assert saved_course.duration_hours == 40
        assert saved_course.modality == "presencial"
    
    def test_course_ec_relationship(self, db_session):
        """Test course-EC standard relationship."""
        # Create EC standard
        ec = ECStandard(code="EC0001", title="Test EC")
        db_session.add(ec)
        db_session.commit()
        
        # Create course
        course = Course(
            name="Test Course",
            ec_standard_id=ec.id,
            ec_code="EC0001",
        )
        db_session.add(course)
        db_session.commit()
        
        # Verify relationship
        course_refreshed = db_session.query(Course).filter_by(name="Test Course").first()
        assert course_refreshed.ec_standard is not None
        assert course_refreshed.ec_standard.code == "EC0001"


class TestTimestamps:
    """Test timestamp functionality."""
    
    def test_timestamp_auto_update(self, db_session):
        """Test automatic timestamp updates."""
        # Create entity
        ec = ECStandard(code="EC0001", title="Test")
        db_session.add(ec)
        db_session.commit()
        
        # Check initial timestamps
        assert ec.created_at is not None
        assert ec.updated_at is not None
        assert ec.first_seen is not None
        assert ec.last_seen is not None
        
        initial_created = ec.created_at
        initial_updated = ec.updated_at
        
        # Update entity
        ec.title = "Updated Test"
        db_session.commit()
        
        # Verify timestamps
        assert ec.created_at == initial_created  # Should not change
        assert ec.updated_at > initial_updated   # Should be updated