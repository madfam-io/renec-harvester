"""
Integration tests for complete harvest workflow.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from datetime import datetime
from pathlib import Path

from scrapy.crawler import CrawlerProcess
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models import ECStandardV2 as ECStandard
from src.models import CertificadorV2 as Certificador
from src.models.centro import Centro
from src.discovery.spiders.renec_spider import RenecSpider
from src.export.exporter import Exporter


class TestHarvestWorkflow:
    """Test complete harvest workflow from crawl to export."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            engine = create_engine(f"sqlite:///{tmp.name}")
            Base.metadata.create_all(engine)
            yield engine
    
    @pytest.fixture
    def db_session(self, temp_db):
        """Create database session."""
        Session = sessionmaker(bind=temp_db)
        session = Session()
        yield session
        session.close()
    
    @pytest.fixture
    def sample_data(self, db_session):
        """Insert sample data into database."""
        # Add EC Standards
        ec1 = ECStandard(
            ec_clave="EC0217",
            titulo="Impartición de cursos de formación del capital humano",
            vigente=True,
            sector="Educación",
            nivel="3",
            descripcion="Estándar para instructores"
        )
        ec2 = ECStandard(
            ec_clave="EC0435",
            titulo="Prestación de servicios de consultoría",
            vigente=True,
            sector="Servicios",
            nivel="2",
            descripcion="Estándar para consultores"
        )
        
        # Add Certificadores
        cert1 = Certificador(
            cert_id="ECE001-99",
            tipo="ECE",
            nombre_legal="CONOCER",
            siglas="CON",
            estado="Ciudad de México",
            estatus="Vigente"
        )
        cert2 = Certificador(
            cert_id="OC002-99",
            tipo="OC",
            nombre_legal="Organismo Certificador",
            siglas="OC",
            estado="Jalisco",
            estatus="Vigente"
        )
        
        # Add Centros
        centro1 = Centro(
            centro_id="CE0001",
            nombre="Centro de Evaluación Tecnológica",
            cert_id="ECE001-99",
            estado="Ciudad de México",
            municipio="Benito Juárez"
        )
        
        db_session.add_all([ec1, ec2, cert1, cert2, centro1])
        db_session.commit()
        
        return {
            "ec_standards": [ec1, ec2],
            "certificadores": [cert1, cert2],
            "centros": [centro1]
        }
    
    @patch('scrapy.crawler.CrawlerProcess')
    def test_crawl_mode(self, mock_crawler_process):
        """Test crawl mode operation."""
        # Mock crawler process
        mock_process = MagicMock()
        mock_crawler_process.return_value = mock_process
        
        # Create spider settings
        settings = {
            'USER_AGENT': 'RENEC Harvester',
            'ROBOTSTXT_OBEY': True,
            'CONCURRENT_REQUESTS': 1,
            'DOWNLOAD_DELAY': 1,
        }
        
        # Initialize crawler
        process = CrawlerProcess(settings)
        
        # Verify crawler was created
        mock_crawler_process.assert_called_once()
        
        # Simulate crawl
        with patch.object(process, 'crawl') as mock_crawl:
            with patch.object(process, 'start') as mock_start:
                process.crawl(RenecSpider, mode='crawl', max_depth=3)
                process.start()
                
                mock_crawl.assert_called_once()
                mock_start.assert_called_once()
    
    def test_harvest_to_database(self, db_session, sample_data):
        """Test harvesting data to database."""
        # Verify data was inserted
        ec_count = db_session.query(ECStandard).count()
        assert ec_count == 2
        
        cert_count = db_session.query(Certificador).count()
        assert cert_count == 2
        
        centro_count = db_session.query(Centro).count()
        assert centro_count == 1
        
        # Verify specific records
        ec = db_session.query(ECStandard).filter_by(ec_clave="EC0217").first()
        assert ec is not None
        assert ec.titulo == "Impartición de cursos de formación del capital humano"
        assert ec.vigente is True
    
    def test_export_workflow(self, db_session, sample_data):
        """Test export workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = Exporter()
            
            # Mock get_session to return our test session
            with patch('src.export.exporter.get_session') as mock_get_session:
                mock_get_session.return_value.__enter__.return_value = db_session
                
                # Export to JSON
                json_path = f"{tmpdir}/harvest.json"
                result = exporter.export_json(
                    json_path,
                    entity_types=["ec_standard", "certificador", "centro"]
                )
                
                # Verify file was created
                assert Path(json_path).exists()
                
                # Verify content
                with open(json_path, 'r') as f:
                    data = json.load(f)
                
                assert "metadata" in data
                assert "ec_standards" in data
                assert "certificadores" in data
                assert "centros" in data
                
                assert len(data["ec_standards"]) == 2
                assert len(data["certificadores"]) == 2
                assert len(data["centros"]) == 1
    
    def test_incremental_harvest(self, db_session):
        """Test incremental harvest functionality."""
        # Add initial data
        ec1 = ECStandard(
            ec_clave="EC0001",
            titulo="Initial Standard",
            vigente=True,
            first_seen=datetime(2024, 1, 1),
            last_seen=datetime(2024, 1, 1)
        )
        db_session.add(ec1)
        db_session.commit()
        
        # Simulate incremental update
        ec1.titulo = "Updated Standard"
        ec1.last_seen = datetime(2024, 1, 2)
        
        # Add new standard
        ec2 = ECStandard(
            ec_clave="EC0002",
            titulo="New Standard",
            vigente=True,
            first_seen=datetime(2024, 1, 2),
            last_seen=datetime(2024, 1, 2)
        )
        db_session.add(ec2)
        db_session.commit()
        
        # Query incremental changes
        recent = db_session.query(ECStandard).filter(
            ECStandard.last_seen >= datetime(2024, 1, 2)
        ).all()
        
        assert len(recent) == 2
        assert any(ec.ec_clave == "EC0002" for ec in recent)
    
    def test_data_validation(self, db_session):
        """Test data validation during harvest."""
        # Try to add invalid EC standard
        with pytest.raises(ValueError):
            ec_invalid = ECStandard(
                ec_clave="INVALID",  # Should start with EC
                titulo="Invalid Standard",
                vigente=True
            )
            # Validation should fail
            ec_invalid.validate_code("ec_clave", "INVALID")
    
    def test_relationship_tracking(self, db_session, sample_data):
        """Test relationship tracking between entities."""
        from src.models.relations import ECEEC, CentroEC
        
        # Add EC-Certificador relationship
        rel1 = ECEEC(
            ec_clave="EC0217",
            cert_id="ECE001-99",
            acreditado_desde=datetime(2020, 1, 1)
        )
        
        # Add Centro-EC relationship
        rel2 = CentroEC(
            centro_id="CE0001",
            ec_clave="EC0217",
            fecha_registro=datetime(2020, 6, 1)
        )
        
        db_session.add_all([rel1, rel2])
        db_session.commit()
        
        # Query relationships
        ec_cert_count = db_session.query(ECEEC).count()
        centro_ec_count = db_session.query(CentroEC).count()
        
        assert ec_cert_count == 1
        assert centro_ec_count == 1
    
    @patch('requests.get')
    def test_api_endpoint_integration(self, mock_requests):
        """Test API endpoint integration."""
        from src.api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Mock database session
        with patch('src.api.dependencies.get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Mock query results
            mock_ec = Mock()
            mock_ec.ec_clave = "EC0217"
            mock_ec.titulo = "Test Standard"
            mock_ec.vigente = True
            
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_ec
            mock_session.query.return_value = mock_query
            
            # Test API call
            response = client.get("/api/v1/ec-standards/EC0217")
            
            assert response.status_code == 200
            data = response.json()
            assert data["ec_clave"] == "EC0217"
    
    def test_performance_monitoring(self):
        """Test performance monitoring during harvest."""
        from src.optimization.performance import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        monitor.reset()
        
        # Simulate harvest operations
        monitor.start_operation("spider_parse", {"url": "test.com"})
        import time
        time.sleep(0.1)
        monitor.end_operation("spider_parse")
        
        monitor.record_metric("items_scraped", 100)
        monitor.record_metric("db_writes", 100)
        
        # Get stats
        stats = monitor.get_stats()
        
        assert "spider_parse" in stats
        assert stats["spider_parse"]["count"] == 1
        assert stats["spider_parse"]["avg_time"] >= 0.1
        
        assert "items_scraped" in stats
        assert stats["items_scraped"]["total"] == 100
    
    def test_error_recovery(self, db_session):
        """Test error recovery during harvest."""
        # Simulate partial harvest with error
        ec1 = ECStandard(
            ec_clave="EC0001",
            titulo="Successfully harvested",
            vigente=True
        )
        db_session.add(ec1)
        db_session.commit()
        
        # Simulate error on second item
        try:
            ec2 = ECStandard(
                ec_clave="EC0002",
                titulo=None,  # Will cause error
                vigente=True
            )
            db_session.add(ec2)
            db_session.commit()
        except Exception:
            db_session.rollback()
        
        # Verify first item was saved
        count = db_session.query(ECStandard).count()
        assert count == 1
        
        # Verify we can continue with more items
        ec3 = ECStandard(
            ec_clave="EC0003",
            titulo="Recovered after error",
            vigente=True
        )
        db_session.add(ec3)
        db_session.commit()
        
        final_count = db_session.query(ECStandard).count()
        assert final_count == 2