"""
Tests for Sectores API endpoints.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.models.sector import Sector
from src.models.comite import Comite
from src.models import ECStandardV2 as ECStandard
from src.models.relations import ECSector


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def sample_sector():
    """Create sample sector."""
    sector = Mock(spec=Sector)
    sector.sector_id = 1
    sector.nombre = "Tecnologías de la Información"
    sector.descripcion = "Sector dedicado al desarrollo y gestión de TI"
    sector.num_comites = 5
    sector.num_estandares = 50
    sector.fecha_creacion = date(2010, 1, 1)
    sector.src_url = "https://conocer.gob.mx/sector/1"
    sector.last_seen = datetime.utcnow()
    sector.first_seen = datetime.utcnow()
    return sector


@pytest.fixture
def sample_comite():
    """Create sample comite."""
    comite = Mock(spec=Comite)
    comite.comite_id = 101
    comite.nombre = "Desarrollo de Software"
    comite.descripcion = "Comité para estándares de desarrollo"
    comite.sector_id = 1
    comite.num_estandares = 15
    comite.fecha_creacion = date(2012, 6, 1)
    comite.src_url = "https://conocer.gob.mx/comite/101"
    comite.last_seen = datetime.utcnow()
    comite.first_seen = datetime.utcnow()
    return comite


class TestSectoresRouter:
    """Test Sectores API endpoints."""
    
    def test_list_sectores(self, client, mock_session, sample_sector):
        """Test listing sectores."""
        mock_query = Mock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_sector]
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/sectores")
                
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sector_id"] == 1
        assert data[0]["nombre"] == "Tecnologías de la Información"
    
    def test_get_sector_detail(self, client, mock_session, sample_sector):
        """Test getting sector details."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_sector
        
        # Mock comites for this sector
        mock_comites_query = Mock()
        mock_comites_query.filter.return_value.all.return_value = [sample_comite]
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[mock_query, mock_comites_query]):
                response = client.get("/api/v1/sectores/1")
                
        assert response.status_code == 200
        data = response.json()
        assert data["sector_id"] == 1
        assert data["nombre"] == "Tecnologías de la Información"
        assert "comites" in data
        assert len(data["comites"]) == 1
    
    def test_get_sector_not_found(self, client, mock_session):
        """Test getting non-existent sector."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/sectores/999")
                
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_sector_comites(self, client, mock_session, sample_sector, sample_comite):
        """Test getting comites for a sector."""
        # Mock sector exists
        mock_query_sector = Mock()
        mock_query_sector.filter.return_value.first.return_value = sample_sector
        
        # Mock comites
        mock_query_comites = Mock()
        mock_query_comites.filter.return_value.all.return_value = [sample_comite]
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_query_sector,    # Sector lookup
                mock_query_comites    # Comites query
            ]):
                response = client.get("/api/v1/sectores/1/comites")
                
        assert response.status_code == 200
        data = response.json()
        assert data["sector_id"] == 1
        assert data["sector_nombre"] == "Tecnologías de la Información"
        assert data["total_comites"] == 1
        assert len(data["comites"]) == 1
        assert data["comites"][0]["comite_id"] == 101
    
    def test_get_sector_ec_standards(self, client, mock_session, sample_sector):
        """Test getting EC standards for a sector."""
        # Mock sector exists
        mock_query_sector = Mock()
        mock_query_sector.filter.return_value.first.return_value = sample_sector
        
        # Mock EC standard
        ec_standard = Mock()
        ec_standard.ec_clave = "EC0217"
        ec_standard.titulo = "Impartición de cursos"
        ec_standard.vigente = True
        ec_standard.nivel = "3"
        ec_standard.comite_id = 101
        
        # Mock EC-Sector relations with join
        mock_relation = Mock()
        mock_relation.ec_clave = "EC0217"
        mock_relation.ECStandardV2 = ec_standard
        
        mock_query_ec = Mock()
        mock_query_ec.join.return_value.filter.return_value.all.return_value = [mock_relation]
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_query_sector,    # Sector lookup
                mock_query_ec        # EC relations with join
            ]):
                response = client.get("/api/v1/sectores/1/ec-standards")
                
        assert response.status_code == 200
        data = response.json()
        assert data["sector_id"] == 1
        assert data["total_estandares"] == 1
        assert len(data["estandares"]) == 1
        assert data["estandares"][0]["ec_clave"] == "EC0217"
        assert data["estandares"][0]["comite_id"] == 101
    
    def test_list_comites(self, client, mock_session, sample_comite):
        """Test listing all comites."""
        mock_query = Mock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_comite]
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/comites")
                
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["comite_id"] == 101
        assert data[0]["nombre"] == "Desarrollo de Software"
    
    def test_list_comites_with_sector_filter(self, client, mock_session):
        """Test listing comites filtered by sector."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/comites?sector_id=2")
                
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_comite_detail(self, client, mock_session, sample_comite, sample_sector):
        """Test getting comite details."""
        mock_query_comite = Mock()
        mock_query_comite.filter.return_value.first.return_value = sample_comite
        
        # Mock sector for this comite
        mock_query_sector = Mock()
        mock_query_sector.filter.return_value.first.return_value = sample_sector
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_query_comite,    # Comite lookup
                mock_query_sector     # Sector lookup
            ]):
                response = client.get("/api/v1/comites/101")
                
        assert response.status_code == 200
        data = response.json()
        assert data["comite_id"] == 101
        assert data["nombre"] == "Desarrollo de Software"
        assert "sector" in data
        assert data["sector"]["sector_id"] == 1
    
    def test_get_comite_ec_standards(self, client, mock_session, sample_comite):
        """Test getting EC standards for a comite."""
        # Mock comite exists
        mock_query_comite = Mock()
        mock_query_comite.filter.return_value.first.return_value = sample_comite
        
        # Mock EC standards
        ec1 = Mock()
        ec1.ec_clave = "EC0217"
        ec1.titulo = "Impartición de cursos"
        ec1.vigente = True
        ec1.nivel = "3"
        
        mock_query_ec = Mock()
        mock_query_ec.filter.return_value.all.return_value = [ec1]
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_query_comite,    # Comite lookup
                mock_query_ec         # EC standards query
            ]):
                response = client.get("/api/v1/comites/101/ec-standards")
                
        assert response.status_code == 200
        data = response.json()
        assert data["comite_id"] == 101
        assert data["total_estandares"] == 1
        assert len(data["estandares"]) == 1
        assert data["estandares"][0]["ec_clave"] == "EC0217"
    
    def test_search_comites(self, client, mock_session, sample_comite):
        """Test searching comites."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_comite]
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', return_value=mock_query):
                response = client.get("/api/v1/comites?search=Software")
                
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    def test_sectores_statistics(self, client, mock_session):
        """Test getting sectores statistics."""
        # Mock sector count
        mock_count = Mock()
        mock_count.count.return_value = 20
        
        # Mock total comites
        mock_comites_count = Mock()
        mock_comites_count.count.return_value = 150
        
        # Mock total ECs
        mock_ec_count = Mock()
        mock_ec_count.count.return_value = 1500
        
        # Mock top sectors by ECs
        mock_top_results = [
            (1, "Tecnologías de la Información", 200),
            (2, "Turismo", 180),
            (3, "Educación", 150)
        ]
        mock_top_query = Mock()
        mock_top_query.join.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_top_results
        
        # Mock date range
        mock_date_result = Mock()
        mock_date_result.one.return_value = (date(2010, 1, 1), date.today())
        mock_date_query = Mock()
        mock_date_query.one.return_value = mock_date_result.one.return_value
        
        with patch('src.api.routers.sectores.get_session', return_value=mock_session):
            with patch.object(mock_session, 'query', side_effect=[
                mock_count,           # Sector count
                mock_comites_count,   # Comites count
                mock_ec_count,        # EC count
                mock_top_query,       # Top sectors
                mock_date_query       # Date range
            ]):
                response = client.get("/api/v1/sectores/stats")
                
        assert response.status_code == 200
        data = response.json()
        assert data["total_sectores"] == 20
        assert data["total_comites"] == 150
        assert data["total_estandares"] == 1500
        assert len(data["top_sectores_por_estandares"]) == 3
        assert data["top_sectores_por_estandares"][0]["nombre"] == "Tecnologías de la Información"
        assert "date_range" in data