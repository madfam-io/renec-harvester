"""
Tests for Certificadores API endpoints.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.models import CertificadorV2 as Certificador
from src.models import ECStandardV2 as ECStandard
from src.models.relations import ECEEC
from src.models.centro import Centro


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def sample_certificador():
    """Create sample certificador."""
    cert = Mock(spec=Certificador)
    cert.cert_id = "ECE001-99"
    cert.tipo = "ECE"
    cert.nombre_legal = "CONOCER"
    cert.siglas = "CON"
    cert.nombre_contacto = "Juan Pérez"
    cert.correo = "contacto@conocer.gob.mx"
    cert.telefono = "555-1234-5678"
    cert.direccion = "Av. Insurgentes Sur 1000"
    cert.municipio = "Benito Juárez"
    cert.estado = "Ciudad de México"
    cert.estado_inegi = "09"
    cert.cp = "03100"
    cert.estatus = "Vigente"
    cert.acreditado_desde = datetime(2020, 1, 1)
    cert.acreditado_hasta = datetime(2025, 12, 31)
    cert.last_seen = datetime.utcnow()
    cert.first_seen = datetime.utcnow()
    return cert


class TestCertificadoresRouter:
    """Test Certificadores API endpoints."""
    
    def test_list_certificadores(self, client, mock_session, sample_certificador):
        """Test listing certificadores."""
        mock_query = Mock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_certificador]
        
        with patch('src.api.routers.certificadores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/certificadores")
                
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["cert_id"] == "ECE001-99"
        assert data[0]["tipo"] == "ECE"
    
    def test_list_certificadores_with_filters(self, client, mock_session):
        """Test listing certificadores with filters."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        with patch('src.api.routers.certificadores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/certificadores?tipo=OC&estado_inegi=09")
                
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_certificador_detail(self, client, mock_session, sample_certificador):
        """Test getting certificador details."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_certificador
        
        # Mock EC standards count
        mock_count_query = Mock()
        mock_count_query.filter.return_value.count.return_value = 15
        
        with patch('src.api.routers.certificadores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[mock_query, mock_count_query]):
                response = client.get("/api/v1/certificadores/ECE001-99")
                
        assert response.status_code == 200
        data = response.json()
        assert data["cert_id"] == "ECE001-99"
        assert data["nombre_legal"] == "CONOCER"
        assert data["num_estandares"] == 15
    
    def test_get_certificador_not_found(self, client, mock_session):
        """Test getting non-existent certificador."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        
        with patch('src.api.routers.certificadores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/certificadores/INVALID")
                
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_certificador_ec_standards(self, client, mock_session, sample_certificador):
        """Test getting EC standards for a certificador."""
        # Mock certificador exists
        mock_query_cert = Mock()
        mock_query_cert.filter.return_value.first.return_value = sample_certificador
        
        # Mock EC standard
        ec_standard = Mock()
        ec_standard.ec_clave = "EC0217"
        ec_standard.titulo = "Impartición de cursos"
        ec_standard.vigente = True
        ec_standard.sector = "Educación"
        ec_standard.nivel = "3"
        
        # Mock ECE relations with join
        mock_relation = Mock()
        mock_relation.ec_clave = "EC0217"
        mock_relation.acreditado_desde = datetime(2020, 1, 1)
        mock_relation.ECStandardV2 = ec_standard
        
        mock_query_ece = Mock()
        mock_query_ece.join.return_value.filter.return_value.all.return_value = [mock_relation]
        
        with patch('src.api.routers.certificadores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_query_cert,    # Certificador lookup
                mock_query_ece      # ECE relations with join
            ]):
                response = client.get("/api/v1/certificadores/ECE001-99/ec-standards")
                
        assert response.status_code == 200
        data = response.json()
        assert data["cert_id"] == "ECE001-99"
        assert data["total_estandares"] == 1
        assert len(data["estandares"]) == 1
        assert data["estandares"][0]["ec_clave"] == "EC0217"
        assert "acreditado_desde" in data["estandares"][0]
    
    def test_get_certificador_centros(self, client, mock_session, sample_certificador):
        """Test getting centros for a certificador."""
        # Mock certificador exists
        mock_query_cert = Mock()
        mock_query_cert.filter.return_value.first.return_value = sample_certificador
        
        # Mock centro
        centro = Mock()
        centro.centro_id = "CE0001"
        centro.nombre = "Centro de Evaluación"
        centro.municipio = "Benito Juárez"
        centro.estado = "Ciudad de México"
        centro.telefono = "555-5678"
        centro.correo = "centro@example.com"
        centro.direccion = "Calle 123"
        
        mock_query_centros = Mock()
        mock_query_centros.filter.return_value.all.return_value = [centro]
        
        with patch('src.api.routers.certificadores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_query_cert,      # Certificador lookup
                mock_query_centros    # Centros query
            ]):
                response = client.get("/api/v1/certificadores/ECE001-99/centros")
                
        assert response.status_code == 200
        data = response.json()
        assert data["cert_id"] == "ECE001-99"
        assert data["total_centros"] == 1
        assert len(data["centros"]) == 1
        assert data["centros"][0]["centro_id"] == "CE0001"
    
    def test_search_certificadores(self, client, mock_session, sample_certificador):
        """Test searching certificadores."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_certificador]
        
        with patch('src.api.routers.certificadores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/certificadores?search=CONOCER")
                
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    def test_certificadores_by_state(self, client, mock_session):
        """Test getting certificadores by state."""
        # Mock certificadores
        cert1 = Mock()
        cert1.cert_id = "ECE001-99"
        cert1.tipo = "ECE"
        cert1.nombre_legal = "Certificador 1"
        cert1.estado = "Ciudad de México"
        cert1.municipio = "Benito Juárez"
        
        cert2 = Mock()
        cert2.cert_id = "OC002-99"
        cert2.tipo = "OC"
        cert2.nombre_legal = "Certificador 2"
        cert2.estado = "Ciudad de México"
        cert2.municipio = "Coyoacán"
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [cert1, cert2]
        
        with patch('src.api.routers.certificadores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/certificadores/by-state/09")
                
        assert response.status_code == 200
        data = response.json()
        assert data["estado_inegi"] == "09"
        assert data["estado_nombre"] == "Ciudad de México"
        assert data["total"] == 2
        assert "by_tipo" in data
        assert "by_municipio" in data
    
    def test_certificadores_statistics(self, client, mock_session):
        """Test getting certificadores statistics."""
        # Mock total count
        mock_count = Mock()
        mock_count.count.return_value = 150
        
        # Mock by tipo
        mock_tipo_results = [
            ("ECE", 100),
            ("OC", 50)
        ]
        mock_tipo_query = Mock()
        mock_tipo_query.group_by.return_value.all.return_value = mock_tipo_results
        
        # Mock by estado
        mock_estado_results = [
            ("Ciudad de México", 30),
            ("Jalisco", 25),
            ("Nuevo León", 20)
        ]
        mock_estado_query = Mock()
        mock_estado_query.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_estado_results
        
        # Mock vigentes count
        mock_vigentes = Mock()
        mock_vigentes.filter.return_value.count.return_value = 140
        
        # Mock date range
        mock_date_result = Mock()
        mock_date_result.one.return_value = (datetime(2015, 1, 1), datetime.utcnow())
        mock_date_query = Mock()
        mock_date_query.one.return_value = mock_date_result.one.return_value
        
        with patch('src.api.routers.certificadores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_count,           # Total count
                mock_tipo_query,      # By tipo
                mock_estado_query,    # By estado
                mock_vigentes,        # Vigentes count
                mock_date_query       # Date range
            ]):
                response = client.get("/api/v1/certificadores/stats")
                
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 150
        assert data["by_tipo"]["ECE"] == 100
        assert data["by_tipo"]["OC"] == 50
        assert len(data["top_estados"]) == 3
        assert data["vigentes"] == 140
        assert "date_range" in data