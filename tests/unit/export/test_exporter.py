"""
Tests for export functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import csv
from datetime import datetime
from pathlib import Path

from src.export.exporter import (
    Exporter,
    ExportFormat,
    ExportStats
)


class TestExporter:
    """Test Exporter functionality."""
    
    @pytest.fixture
    def exporter(self):
        """Create exporter instance."""
        return Exporter()
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = MagicMock()
        return session
    
    @pytest.fixture
    def sample_ec_standards(self):
        """Create sample EC standards."""
        ec1 = Mock()
        ec1.ec_clave = "EC0217"
        ec1.titulo = "Impartición de cursos"
        ec1.vigente = True
        ec1.sector = "Educación"
        ec1.nivel = "3"
        ec1.to_dict.return_value = {
            "ec_clave": "EC0217",
            "titulo": "Impartición de cursos",
            "vigente": True,
            "sector": "Educación",
            "nivel": "3"
        }
        
        ec2 = Mock()
        ec2.ec_clave = "EC0435"
        ec2.titulo = "Prestación de servicios"
        ec2.vigente = True
        ec2.sector = "Servicios"
        ec2.nivel = "2"
        ec2.to_dict.return_value = {
            "ec_clave": "EC0435",
            "titulo": "Prestación de servicios",
            "vigente": True,
            "sector": "Servicios",
            "nivel": "2"
        }
        
        return [ec1, ec2]
    
    @patch('src.export.exporter.get_session')
    @patch('builtins.open', new_callable=mock_open)
    def test_export_json(self, mock_file, mock_get_session, exporter, mock_session, sample_ec_standards):
        """Test JSON export."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_query = Mock()
        mock_query.all.return_value = sample_ec_standards
        mock_session.query.return_value = mock_query
        
        # Export
        output_path = exporter.export_json("/tmp/test.json", ["ec_standard"])
        
        # Verify file was written
        mock_file.assert_called_once_with("/tmp/test.json", "w", encoding="utf-8")
        
        # Verify JSON structure
        written_data = ""
        for call in mock_file().write.call_args_list:
            written_data += call[0][0]
        
        data = json.loads(written_data)
        assert "metadata" in data
        assert "ec_standards" in data
        assert len(data["ec_standards"]) == 2
        assert data["ec_standards"][0]["ec_clave"] == "EC0217"
    
    @patch('src.export.exporter.get_session')
    @patch('builtins.open', new_callable=mock_open)
    def test_export_csv(self, mock_file, mock_get_session, exporter, mock_session, sample_ec_standards):
        """Test CSV export."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_query = Mock()
        mock_query.all.return_value = sample_ec_standards
        mock_session.query.return_value = mock_query
        
        # Export
        output_paths = exporter.export_csv("/tmp/test", ["ec_standard"])
        
        # Verify file was created
        assert "/tmp/test_ec_standards.csv" in output_paths
        mock_file.assert_called()
    
    @patch('src.export.exporter.get_session')
    def test_export_sqlite(self, mock_get_session, exporter, mock_session, sample_ec_standards):
        """Test SQLite export."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_query = Mock()
        mock_query.all.return_value = sample_ec_standards
        mock_session.query.return_value = mock_query
        
        with patch('sqlite3.connect') as mock_sqlite:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_sqlite.return_value = mock_conn
            
            # Export
            output_path = exporter.export_sqlite("/tmp/test.db", ["ec_standard"])
            
            # Verify SQLite operations
            mock_sqlite.assert_called_once_with("/tmp/test.db")
            assert mock_cursor.execute.called
            assert mock_conn.commit.called
    
    @patch('src.export.exporter.get_session')
    @patch('builtins.open', new_callable=mock_open)
    def test_export_graph_json(self, mock_file, mock_get_session, exporter, mock_session):
        """Test graph JSON export."""
        # Mock EC standards
        ec1 = Mock()
        ec1.ec_clave = "EC0217"
        ec1.titulo = "Impartición de cursos"
        ec1.sector_id = 1
        ec1.to_dict.return_value = {"ec_clave": "EC0217", "titulo": "Impartición de cursos"}
        
        # Mock certificadores
        cert1 = Mock()
        cert1.cert_id = "ECE001-99"
        cert1.nombre_legal = "CONOCER"
        cert1.to_dict.return_value = {"cert_id": "ECE001-99", "nombre_legal": "CONOCER"}
        
        # Mock relations
        relation = Mock()
        relation.ec_clave = "EC0217"
        relation.cert_id = "ECE001-99"
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Setup query responses
        def mock_query(model):
            query = Mock()
            if "ECStandardV2" in str(model):
                query.all.return_value = [ec1]
            elif "CertificadorV2" in str(model):
                query.all.return_value = [cert1]
            elif "ECEEC" in str(model):
                query.all.return_value = [relation]
            else:
                query.all.return_value = []
            return query
        
        mock_session.query.side_effect = mock_query
        
        # Export
        output_path = exporter.export_graph_json("/tmp/graph.json")
        
        # Verify file was written
        mock_file.assert_called_once_with("/tmp/graph.json", "w", encoding="utf-8")
        
        # Verify graph structure
        written_data = ""
        for call in mock_file().write.call_args_list:
            written_data += call[0][0]
        
        data = json.loads(written_data)
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2  # EC + Certificador
        assert len(data["edges"]) == 1  # Relation
    
    @patch('src.export.exporter.get_session')
    @patch('builtins.open', new_callable=mock_open)
    def test_export_denormalized_json(self, mock_file, mock_get_session, exporter, mock_session):
        """Test denormalized JSON export."""
        # Mock EC standard with relations
        ec1 = Mock()
        ec1.ec_clave = "EC0217"
        ec1.titulo = "Impartición de cursos"
        ec1.to_dict.return_value = {
            "ec_clave": "EC0217",
            "titulo": "Impartición de cursos"
        }
        
        # Mock related data
        cert_relation = Mock()
        cert_relation.cert_id = "ECE001-99"
        
        centro_relation = Mock()
        centro_relation.centro_id = "CE0001"
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Setup queries
        ec_query = Mock()
        ec_query.all.return_value = [ec1]
        
        cert_rel_query = Mock()
        cert_rel_query.filter.return_value.all.return_value = [cert_relation]
        
        centro_rel_query = Mock()
        centro_rel_query.filter.return_value.all.return_value = [centro_relation]
        
        # Mock the query method to return different results based on the model
        query_call_count = 0
        def mock_query(model):
            nonlocal query_call_count
            query_call_count += 1
            if query_call_count == 1:  # First call for EC standards
                return ec_query
            elif query_call_count == 2:  # Second call for cert relations
                return cert_rel_query
            else:  # Third call for centro relations
                return centro_rel_query
        
        mock_session.query.side_effect = mock_query
        
        # Export
        output_path = exporter.export_denormalized_json("/tmp/denorm.json", ["ec_standard"])
        
        # Verify
        mock_file.assert_called_once()
        written_data = ""
        for call in mock_file().write.call_args_list:
            written_data += call[0][0]
        
        data = json.loads(written_data)
        assert "ec_standards" in data
        assert len(data["ec_standards"]) == 1
        assert "certificadores" in data["ec_standards"][0]
        assert "centros" in data["ec_standards"][0]
    
    def test_export_with_filters(self, exporter):
        """Test export with filters."""
        filters = {
            "vigente": True,
            "sector": "Educación",
            "nivel": [2, 3]
        }
        
        # Mock query
        mock_query = Mock()
        
        # Apply filters
        filtered_query = exporter._apply_filters(mock_query, "ECStandardV2", filters)
        
        # Verify filter was called
        assert mock_query.filter.called
    
    def test_export_stats(self, exporter):
        """Test export statistics."""
        stats = ExportStats()
        stats.total_records = 100
        stats.export_time = 5.5
        stats.file_size = 1024 * 1024  # 1MB
        
        summary = stats.get_summary()
        
        assert summary["total_records"] == 100
        assert summary["export_time"] == 5.5
        assert summary["file_size_mb"] == 1.0
        assert summary["records_per_second"] == pytest.approx(18.18, 0.01)
    
    @patch('src.export.exporter.get_session')
    def test_validate_export(self, mock_get_session, exporter, mock_session):
        """Test export validation."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock counts
        mock_query = Mock()
        mock_query.count.return_value = 100
        mock_session.query.return_value = mock_query
        
        # Mock file
        with patch('pathlib.Path') as mock_path:
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_file.stat.return_value.st_size = 1024
            mock_path.return_value = mock_file
            
            # Validate
            is_valid, issues = exporter.validate_export("/tmp/test.json", ["ec_standard"])
            
            assert is_valid is True
            assert len(issues) == 0
    
    def test_incremental_export(self, exporter):
        """Test incremental export functionality."""
        # Create mock query
        mock_query = Mock()
        
        # Apply incremental filter
        since = datetime(2024, 1, 1)
        filtered = exporter._apply_incremental_filter(
            mock_query, 
            "ECStandardV2", 
            since
        )
        
        # Verify filter was applied
        assert mock_query.filter.called
    
    def test_export_format_enum(self):
        """Test ExportFormat enum."""
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.SQLITE.value == "sqlite"
        assert ExportFormat.GRAPH_JSON.value == "graph_json"
        assert ExportFormat.DENORMALIZED_JSON.value == "denormalized_json"