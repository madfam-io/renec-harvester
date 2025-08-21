"""
Tests for Search API endpoints.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.models import ECStandardV2 as ECStandard
from src.models import CertificadorV2 as Certificador
from src.models.centro import Centro


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    return Mock()


class TestSearchRouter:
    """Test Search API endpoints."""
    
    def test_search_all_entities(self, client, mock_session):
        """Test cross-entity search."""
        # Mock EC standards results
        ec_standard = Mock()
        ec_standard.ec_clave = "EC0217"
        ec_standard.titulo = "Impartición de cursos"
        ec_standard.vigente = True
        ec_standard.sector = "Educación"
        ec_standard.nivel = "3"
        
        # Mock certificadores results
        certificador = Mock()
        certificador.cert_id = "ECE001-99"
        certificador.tipo = "ECE"
        certificador.nombre_legal = "CONOCER"
        certificador.siglas = "CON"
        certificador.estado = "Ciudad de México"
        certificador.estatus = "Vigente"
        
        # Setup mock queries
        mock_ec_query = Mock()
        mock_ec_query.filter.return_value.limit.return_value.all.return_value = [ec_standard]
        
        mock_cert_query = Mock()
        mock_cert_query.filter.return_value.limit.return_value.all.return_value = [certificador]
        
        mock_centro_query = Mock()
        mock_centro_query.filter.return_value.limit.return_value.all.return_value = []
        
        with patch('src.api.routers.search.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_ec_query,
                mock_cert_query,
                mock_centro_query,
                Mock().filter.return_value.limit.return_value.all.return_value,  # sectores
                Mock().filter.return_value.limit.return_value.all.return_value   # comites
            ]):
                response = client.get("/api/v1/search?q=test")
                
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert data["total_results"] == 2
        assert "ec_standards" in data["results"]
        assert data["results"]["ec_standards"]["count"] == 1
        assert "certificadores" in data["results"]
        assert data["results"]["certificadores"]["count"] == 1
    
    def test_search_minimum_query_length(self, client):
        """Test search with query too short."""
        response = client.get("/api/v1/search?q=a")
        assert response.status_code == 422  # Validation error
    
    def test_search_with_entity_filter(self, client, mock_session):
        """Test search with specific entity types."""
        mock_query = Mock()
        mock_query.filter.return_value.limit.return_value.all.return_value = []
        
        with patch('src.api.routers.search.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/search?q=test&entity_types=ec_standards,certificadores")
                
        assert response.status_code == 200
        data = response.json()
        assert "ec_standards" in data["results"]
        assert "certificadores" in data["results"]
        assert "centros" not in data["results"]
    
    def test_search_suggestions(self, client, mock_session):
        """Test search suggestions endpoint."""
        # Mock EC standard for suggestions
        mock_result = Mock()
        mock_result.ec_clave = "EC0217"
        mock_result.titulo = "Impartición de cursos de formación"
        
        mock_query = Mock()
        mock_query.filter.return_value.limit.return_value.all.return_value = [(mock_result.ec_clave, mock_result.titulo)]
        
        with patch('src.api.routers.search.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/search/suggest?q=EC02&entity_type=ec_standards")
                
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "EC02"
        assert data["entity_type"] == "ec_standards"
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["value"] == "EC0217"
    
    def test_search_by_location(self, client, mock_session):
        """Test location-based search."""
        # Mock certificador
        certificador = Mock()
        certificador.cert_id = "ECE001-99"
        certificador.tipo = "ECE"
        certificador.nombre_legal = "CONOCER"
        certificador.municipio = "Benito Juárez"
        certificador.telefono = "555-1234"
        certificador.correo = "info@conocer.gob.mx"
        certificador.estado = "Ciudad de México"
        
        # Mock centro
        centro = Mock()
        centro.centro_id = "CE0001"
        centro.nombre = "Centro de Evaluación"
        centro.municipio = "Benito Juárez"
        centro.telefono = "555-5678"
        centro.correo = "centro@example.com"
        
        mock_cert_query = Mock()
        mock_cert_query.filter.return_value.all.return_value = [certificador]
        
        mock_centro_query = Mock()
        mock_centro_query.filter.return_value.all.return_value = [centro]
        
        with patch('src.api.routers.search.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_cert_query,
                mock_centro_query,
                mock_cert_query  # For estado lookup
            ]):
                response = client.get("/api/v1/search/by-location?estado_inegi=09")
                
        assert response.status_code == 200
        data = response.json()
        assert data["location"]["estado_inegi"] == "09"
        assert data["location"]["estado_nombre"] == "Ciudad de México"
        assert "certificadores" in data["results"]
        assert data["results"]["certificadores"]["count"] == 1
        assert "centros" in data["results"]
        assert data["results"]["centros"]["count"] == 1
    
    def test_search_related_entities(self, client, mock_session):
        """Test finding related entities."""
        # Mock EC standard
        ec_standard = Mock()
        ec_standard.ec_clave = "EC0217"
        ec_standard.titulo = "Impartición de cursos"
        ec_standard.vigente = True
        ec_standard.sector_id = 1
        ec_standard.comite_id = 1
        
        mock_ec_query = Mock()
        mock_ec_query.filter.return_value.first.return_value = ec_standard
        
        # Mock related entities
        mock_ece_relations = [Mock(cert_id="ECE001-99")]
        mock_centro_relations = [Mock(centro_id="CE0001")]
        
        mock_relation_query = Mock()
        mock_relation_query.filter.return_value.all.return_value = mock_ece_relations
        
        mock_centro_rel_query = Mock()
        mock_centro_rel_query.filter.return_value.all.return_value = mock_centro_relations
        
        # Mock entity lookups
        mock_cert = Mock()
        mock_cert.cert_id = "ECE001-99"
        mock_cert.nombre_legal = "CONOCER"
        mock_cert.tipo = "ECE"
        mock_cert.estado = "Ciudad de México"
        
        mock_cert_lookup = Mock()
        mock_cert_lookup.filter.return_value.all.return_value = [mock_cert]
        
        mock_centro = Mock()
        mock_centro.centro_id = "CE0001"
        mock_centro.nombre = "Centro de Evaluación"
        mock_centro.estado = "Ciudad de México"
        mock_centro.municipio = "Benito Juárez"
        
        mock_centro_lookup = Mock()
        mock_centro_lookup.filter.return_value.all.return_value = [mock_centro]
        
        with patch('src.api.routers.search.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_ec_query,          # EC lookup
                mock_relation_query,    # ECE relations
                mock_cert_lookup,       # Certificador lookup
                mock_centro_rel_query,  # Centro relations
                mock_centro_lookup,     # Centro lookup
                Mock().filter.return_value.first.return_value,  # Sector
                Mock().filter.return_value.first.return_value   # Comite
            ]):
                response = client.get("/api/v1/search/related/ec_standard/EC0217")
                
        assert response.status_code == 200
        data = response.json()
        assert "ec_standard" in data
        assert data["ec_standard"]["ec_clave"] == "EC0217"
        assert "certificadores" in data
        assert data["certificadores"]["count"] == 1
        assert "centros" in data
        assert data["centros"]["count"] == 1
    
    def test_search_related_not_found(self, client, mock_session):
        """Test related entities for non-existent entity."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        
        with patch('src.api.routers.search.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/search/related/ec_standard/INVALID")
                
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert "not found" in data["error"]