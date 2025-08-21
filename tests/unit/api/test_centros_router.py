"""
Tests for Centros API endpoints.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.models.centro import Centro
from src.models import ECStandardV2 as ECStandard
from src.models.relations import CentroEC


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def sample_centro():
    """Create sample centro."""
    centro = Mock(spec=Centro)
    centro.centro_id = "CE0001"
    centro.nombre = "Centro de Evaluación Tecnológica"
    centro.cert_id = "ECE001-99"
    centro.nombre_contacto = "María García"
    centro.correo = "contacto@centro-eval.mx"
    centro.telefono = "555-9876-5432"
    centro.direccion = "Av. Reforma 200"
    centro.municipio = "Cuauhtémoc"
    centro.estado = "Ciudad de México"
    centro.estado_inegi = "09"
    centro.cp = "06600"
    centro.latitud = 19.4326
    centro.longitud = -99.1332
    centro.last_seen = datetime.utcnow()
    centro.first_seen = datetime.utcnow()
    return centro


class TestCentrosRouter:
    """Test Centros API endpoints."""
    
    def test_list_centros(self, client, mock_session, sample_centro):
        """Test listing centros."""
        mock_query = Mock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_centro]
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/centros")
                
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["centro_id"] == "CE0001"
        assert data[0]["nombre"] == "Centro de Evaluación Tecnológica"
    
    def test_list_centros_with_filters(self, client, mock_session):
        """Test listing centros with filters."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/centros?estado_inegi=09&cert_id=ECE001-99")
                
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_centro_detail(self, client, mock_session, sample_centro):
        """Test getting centro details."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_centro
        
        # Mock EC standards count
        mock_count_query = Mock()
        mock_count_query.filter.return_value.count.return_value = 10
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[mock_query, mock_count_query]):
                response = client.get("/api/v1/centros/CE0001")
                
        assert response.status_code == 200
        data = response.json()
        assert data["centro_id"] == "CE0001"
        assert data["nombre"] == "Centro de Evaluación Tecnológica"
        assert data["num_estandares"] == 10
    
    def test_get_centro_not_found(self, client, mock_session):
        """Test getting non-existent centro."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/centros/INVALID")
                
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_centro_ec_standards(self, client, mock_session, sample_centro):
        """Test getting EC standards for a centro."""
        # Mock centro exists
        mock_query_centro = Mock()
        mock_query_centro.filter.return_value.first.return_value = sample_centro
        
        # Mock EC standard
        ec_standard = Mock()
        ec_standard.ec_clave = "EC0217"
        ec_standard.titulo = "Impartición de cursos"
        ec_standard.vigente = True
        ec_standard.sector = "Educación"
        ec_standard.nivel = "3"
        
        # Mock centro-EC relations with join
        mock_relation = Mock()
        mock_relation.ec_clave = "EC0217"
        mock_relation.fecha_registro = datetime(2020, 6, 1)
        mock_relation.ECStandardV2 = ec_standard
        
        mock_query_ec = Mock()
        mock_query_ec.join.return_value.filter.return_value.all.return_value = [mock_relation]
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_query_centro,    # Centro lookup
                mock_query_ec        # EC relations with join
            ]):
                response = client.get("/api/v1/centros/CE0001/ec-standards")
                
        assert response.status_code == 200
        data = response.json()
        assert data["centro_id"] == "CE0001"
        assert data["total_estandares"] == 1
        assert len(data["estandares"]) == 1
        assert data["estandares"][0]["ec_clave"] == "EC0217"
        assert "fecha_registro" in data["estandares"][0]
    
    def test_search_centros(self, client, mock_session, sample_centro):
        """Test searching centros."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_centro]
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/centros?search=Tecnológica")
                
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    def test_centros_by_state(self, client, mock_session):
        """Test getting centros by state."""
        # Mock centros
        centro1 = Mock()
        centro1.centro_id = "CE0001"
        centro1.nombre = "Centro 1"
        centro1.municipio = "Cuauhtémoc"
        centro1.estado = "Ciudad de México"
        centro1.cert_id = "ECE001-99"
        
        centro2 = Mock()
        centro2.centro_id = "CE0002"
        centro2.nombre = "Centro 2"
        centro2.municipio = "Miguel Hidalgo"
        centro2.estado = "Ciudad de México"
        centro2.cert_id = "OC002-99"
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [centro1, centro2]
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/centros/by-state/09")
                
        assert response.status_code == 200
        data = response.json()
        assert data["estado_inegi"] == "09"
        assert data["estado_nombre"] == "Ciudad de México"
        assert data["total"] == 2
        assert "by_municipio" in data
        assert "by_certificador" in data
    
    def test_centros_by_certificador(self, client, mock_session):
        """Test getting centros by certificador."""
        # Mock centros
        centro1 = Mock()
        centro1.centro_id = "CE0001"
        centro1.nombre = "Centro 1"
        centro1.estado = "Ciudad de México"
        centro1.municipio = "Cuauhtémoc"
        
        centro2 = Mock()
        centro2.centro_id = "CE0002"
        centro2.nombre = "Centro 2"
        centro2.estado = "Jalisco"
        centro2.municipio = "Guadalajara"
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [centro1, centro2]
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/centros/by-certificador/ECE001-99")
                
        assert response.status_code == 200
        data = response.json()
        assert data["cert_id"] == "ECE001-99"
        assert data["total"] == 2
        assert "by_estado" in data
        assert len(data["centros"]) == 2
    
    def test_centros_nearby(self, client, mock_session):
        """Test finding nearby centros."""
        # Mock centros with distance calculation
        centro1 = Mock()
        centro1.centro_id = "CE0001"
        centro1.nombre = "Centro Cercano"
        centro1.direccion = "Av. Reforma 200"
        centro1.municipio = "Cuauhtémoc"
        centro1.estado = "Ciudad de México"
        centro1.telefono = "555-1234"
        centro1.correo = "centro1@example.com"
        centro1.latitud = 19.4326
        centro1.longitud = -99.1332
        
        # Mock the result with distance
        mock_result = Mock()
        mock_result.Centro = centro1
        mock_result.distance = 1.5  # km
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_result]
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/centros/nearby?lat=19.4300&lon=-99.1300&radius=5")
                
        assert response.status_code == 200
        data = response.json()
        assert data["location"]["lat"] == 19.43
        assert data["location"]["lon"] == -99.13
        assert data["radius_km"] == 5
        assert data["total"] == 1
        assert len(data["centros"]) == 1
        assert data["centros"][0]["centro_id"] == "CE0001"
        assert data["centros"][0]["distance_km"] == 1.5
    
    def test_centros_statistics(self, client, mock_session):
        """Test getting centros statistics."""
        # Mock total count
        mock_count = Mock()
        mock_count.count.return_value = 500
        
        # Mock by estado
        mock_estado_results = [
            ("Ciudad de México", 100),
            ("Estado de México", 80),
            ("Jalisco", 60)
        ]
        mock_estado_query = Mock()
        mock_estado_query.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_estado_results
        
        # Mock by certificador
        mock_cert_results = [
            ("ECE001-99", 150),
            ("OC002-99", 100)
        ]
        mock_cert_query = Mock()
        mock_cert_query.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_cert_results
        
        # Mock average ECs
        mock_avg_result = Mock()
        mock_avg_result.scalar.return_value = 8.5
        
        # Mock date range
        mock_date_result = Mock()
        mock_date_result.one.return_value = (datetime(2018, 1, 1), datetime.utcnow())
        mock_date_query = Mock()
        mock_date_query.one.return_value = mock_date_result.one.return_value
        
        with patch('src.api.routers.centros.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_count,           # Total count
                mock_estado_query,    # By estado
                mock_cert_query,      # By certificador
                mock_avg_result,      # Average ECs
                mock_date_query       # Date range
            ]):
                response = client.get("/api/v1/centros/stats")
                
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 500
        assert len(data["top_estados"]) == 3
        assert len(data["top_certificadores"]) == 2
        assert data["avg_estandares_por_centro"] == 8.5
        assert "date_range" in data