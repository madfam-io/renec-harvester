"""Pytest configuration and fixtures."""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.utils.cache import RedisCache


@pytest.fixture(scope="session")
def test_db_url():
    """Test database URL."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine(test_db_url):
    """Create test database engine."""
    engine = create_engine(test_db_url)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_redis():
    """Mock Redis cache."""
    cache = MagicMock(spec=RedisCache)
    cache.get.return_value = None
    cache.set.return_value = True
    cache.exists.return_value = 0
    cache.delete.return_value = 1
    return cache


@pytest.fixture
def sample_ec_standard():
    """Sample EC standard data."""
    return {
        "type": "ec_standard",
        "code": "EC0001",
        "title": "Competencia en desarrollo de software",
        "sector": "Tecnología",
        "level": 3,
        "publication_date": "2023-01-15",
        "url": "https://conocer.gob.mx/ec0001",
    }


@pytest.fixture
def sample_certificador():
    """Sample certificador data."""
    return {
        "type": "certificador",
        "code": "OC001",
        "name": "Centro de Certificación Tecnológica",
        "rfc": "CCT123456ABC",
        "contact_email": "contacto@certificador.mx",
        "contact_phone": "+525555555555",
        "address": "Av. Principal 123",
        "city": "Ciudad de México",
        "state": "Ciudad de México",
        "url": "https://conocer.gob.mx/oc001",
    }


@pytest.fixture
def sample_center():
    """Sample evaluation center data."""
    return {
        "type": "center",
        "code": "CE00001",
        "name": "Centro de Evaluación Norte",
        "certificador_code": "OC001",
        "contact_email": "centro@evaluacion.mx",
        "contact_phone": "+525544444444",
        "address": "Calle Secundaria 456",
        "city": "Monterrey",
        "state": "Nuevo León",
        "url": "https://conocer.gob.mx/ce00001",
    }


@pytest.fixture
def sample_course():
    """Sample course data."""
    return {
        "type": "course",
        "name": "Curso de preparación EC0001",
        "ec_code": "EC0001",
        "duration": "40 horas",
        "modality": "presencial",
        "start_date": "2024-01-15",
        "provider_name": "Instituto de Capacitación",
        "city": "Guadalajara",
        "state": "Jalisco",
        "url": "https://conocer.gob.mx/curso/ec0001",
    }


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Set up test environment."""
    # Create test directories
    test_dirs = ["artifacts", "logs"]
    for dir_name in test_dirs:
        (tmp_path / dir_name).mkdir()
    
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    
    # Set test environment variables
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    
    yield tmp_path