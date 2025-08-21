"""
Tests for EC Standards API endpoints.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.models import ECStandardV2 as ECStandard
from src.models import CertificadorV2 as Certificador
from src.models.relations import ECEEC, CentroEC


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def sample_ec_standard():
    """Create sample EC standard."""
    ec = Mock(spec=ECStandard)
    ec.ec_clave = "EC0217"
    ec.titulo = "Impartición de cursos de formación del capital humano"
    ec.version = "3.00"
    ec.vigente = True
    ec.sector = "Educación"
    ec.sector_id = 1
    ec.nivel = "3"
    ec.duracion_horas = 40
    ec.last_seen = datetime.utcnow()
    ec.first_seen = datetime.utcnow()
    ec.comite = "Gestión y desarrollo de capital humano"
    ec.comite_id = 1
    ec.descripcion = "Test description"
    ec.competencias = ["Competencia 1", "Competencia 2"]
    return ec


@pytest.fixture
def sample_certificador():
    """Create sample certificador."""
    cert = Mock(spec=Certificador)
    cert.cert_id = "ECE001-99"
    cert.tipo = "ECE"
    cert.nombre_legal = "CONOCER"
    cert.estado = "Ciudad de México"
    return cert


class TestECStandardsRouter:
    """Test EC Standards API endpoints."""
    
    def test_list_ec_standards(self, client, mock_session, sample_ec_standard):
        """Test listing EC standards."""
        # Mock query chain
        mock_query = Mock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_ec_standard]
        
        with patch('src.api.routers.ec_standards.get_session', return_value=mock_session):
            with patch.object(mock_session, 'execute', return_value=mock_result):
                response = client.get("/api/v1/ec-standards")
                
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["ec_clave"] == "EC0217"
        assert data[0]["vigente"] is True
    
    def test_list_ec_standards_with_filters(self, client, mock_session):
        """Test listing EC standards with filters."""
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        
        with patch('src.api.routers.ec_standards.get_session', return_value=mock_session):
            with patch.object(mock_session, 'execute', return_value=mock_result):
                response = client.get("/api/v1/ec-standards?vigente=true&sector_id=1")
                
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_ec_standard_detail(self, client, mock_session, sample_ec_standard):
        """Test getting EC standard details."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_ec_standard
        
        # Mock related certificadores
        mock_ece_relations = [Mock(cert_id="ECE001-99")]
        mock_query_ece = Mock()
        mock_query_ece.filter.return_value.all.return_value = mock_ece_relations
        
        with patch('src.api.routers.ec_standards.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[mock_query, mock_query_ece, mock_query]):
                response = client.get("/api/v1/ec-standards/EC0217")
                
        assert response.status_code == 200
        data = response.json()
        assert data["ec_clave"] == "EC0217"
        assert data["titulo"] == "Impartición de cursos de formación del capital humano"
        assert "certificadores" in data
    
    def test_get_ec_standard_not_found(self, client, mock_session):
        """Test getting non-existent EC standard."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        
        with patch('src.api.routers.ec_standards.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/ec-standards/INVALID")
                
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_ec_certificadores(self, client, mock_session, sample_ec_standard, sample_certificador):
        """Test getting certificadores for an EC standard."""
        # Mock EC exists
        mock_query_ec = Mock()
        mock_query_ec.filter.return_value.first.return_value = sample_ec_standard
        
        # Mock ECE relations
        mock_relation = Mock()
        mock_relation.cert_id = "ECE001-99"
        mock_relation.acreditado_desde = datetime.utcnow()
        
        mock_query_ece = Mock()
        mock_query_ece.filter.return_value.all.return_value = [mock_relation]
        
        # Mock certificador lookup
        mock_query_cert = Mock()
        mock_query_cert.filter.return_value.first.return_value = sample_certificador
        
        with patch('src.api.routers.ec_standards.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_query_ec,    # EC lookup
                mock_query_ece,   # ECE relations
                mock_query_cert   # Certificador lookup
            ]):
                response = client.get("/api/v1/ec-standards/EC0217/certificadores")
                
        assert response.status_code == 200
        data = response.json()
        assert data["ec_clave"] == "EC0217"
        assert data["total_certificadores"] == 1
        assert len(data["certificadores"]) == 1
        assert data["certificadores"][0]["cert_id"] == "ECE001-99"
    
    def test_get_ec_centros(self, client, mock_session, sample_ec_standard):
        """Test getting centros for an EC standard."""
        # Mock EC exists
        mock_query_ec = Mock()
        mock_query_ec.filter.return_value.first.return_value = sample_ec_standard
        
        # Mock centro with join
        mock_centro = Mock()
        mock_centro.centro_id = "CE0001"
        mock_centro.nombre = "Centro de Evaluación"
        mock_centro.estado = "Ciudad de México"
        mock_centro.estado_inegi = "09"
        mock_centro.municipio = "Benito Juárez"
        mock_centro.telefono = "555-1234"
        mock_centro.correo = "centro@example.com"
        
        mock_query_centros = Mock()
        mock_query_centros.join.return_value.filter.return_value.all.return_value = [mock_centro]
        
        with patch('src.api.routers.ec_standards.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_query_ec,       # EC lookup
                mock_query_centros   # Centros query
            ]):
                response = client.get("/api/v1/ec-standards/EC0217/centros")
                
        assert response.status_code == 200
        data = response.json()
        assert data["ec_clave"] == "EC0217"
        assert data["total_centros"] == 1
        assert len(data["centros"]) == 1
        assert data["centros"][0]["centro_id"] == "CE0001"
    
    def test_search_ec_standards(self, client, mock_session, sample_ec_standard):
        """Test searching EC standards."""
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_ec_standard]
        
        with patch('src.api.routers.ec_standards.get_session', return_value=mock_session):
            with patch.object(mock_session, 'execute', return_value=mock_result):
                response = client.get("/api/v1/ec-standards?search=formación")
                
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    def test_pagination(self, client, mock_session):
        """Test pagination parameters."""
        mock_query = Mock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        
        with patch('src.api.routers.ec_standards.get_session', return_value=mock_session):
            with patch.object(mock_session, 'execute', return_value=mock_result):
                response = client.get("/api/v1/ec-standards?skip=10&limit=20")
                
        assert response.status_code == 200
        # Verify offset and limit were called
        mock_query.offset.assert_called_with(10)
        mock_query.limit.assert_called_with(20)