"""Data export functionality."""

import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from structlog import get_logger

from src.models import get_session
from src.models.components import ECStandard, Certificador, EvaluationCenter, Course

logger = get_logger()


class DataExporter:
    """Export harvested data to various formats."""
    
    def __init__(self):
        self.exporters = {
            "json": self._export_json,
            "csv": self._export_csv,
            "parquet": self._export_parquet,
            "excel": self._export_excel,
        }
    
    def export_harvest(self, session_id: str, format: str, output_dir: Path) -> List[Path]:
        """Export harvest data to specified format."""
        if format not in self.exporters:
            raise ValueError(f"Unsupported format: {format}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get data from database
        data = self._load_harvest_data(session_id)
        
        # Export using appropriate method
        exporter = self.exporters[format]
        return exporter(data, output_dir, session_id)
    
    def _load_harvest_data(self, session_id: str) -> Dict[str, pd.DataFrame]:
        """Load harvest data from database."""
        data = {}
        
        with get_session() as session:
            # Load EC Standards
            ec_standards = session.query(ECStandard).all()
            data["ec_standards"] = pd.DataFrame([
                {
                    "code": ec.code,
                    "title": ec.title,
                    "sector": ec.sector,
                    "level": ec.level,
                    "publication_date": ec.publication_date,
                    "status": ec.status,
                    "url": ec.url,
                    "first_seen": ec.first_seen,
                    "last_seen": ec.last_seen,
                }
                for ec in ec_standards
            ])
            
            # Load Certificadores
            certificadores = session.query(Certificador).all()
            data["certificadores"] = pd.DataFrame([
                {
                    "code": cert.code,
                    "name": cert.name,
                    "rfc": cert.rfc,
                    "contact_email": cert.contact_email,
                    "contact_phone": cert.contact_phone,
                    "address": cert.address,
                    "city": cert.city,
                    "state": cert.state,
                    "status": cert.status,
                    "url": cert.url,
                    "first_seen": cert.first_seen,
                    "last_seen": cert.last_seen,
                }
                for cert in certificadores
            ])
            
            # Load Evaluation Centers
            centers = session.query(EvaluationCenter).all()
            data["evaluation_centers"] = pd.DataFrame([
                {
                    "code": center.code,
                    "name": center.name,
                    "certificador_code": center.certificador_code,
                    "contact_email": center.contact_email,
                    "contact_phone": center.contact_phone,
                    "address": center.address,
                    "city": center.city,
                    "state": center.state,
                    "status": center.status,
                    "url": center.url,
                    "first_seen": center.first_seen,
                    "last_seen": center.last_seen,
                }
                for center in centers
            ])
            
            # Load Courses
            courses = session.query(Course).all()
            data["courses"] = pd.DataFrame([
                {
                    "name": course.name,
                    "ec_code": course.ec_code,
                    "duration_hours": course.duration_hours,
                    "modality": course.modality,
                    "start_date": course.start_date,
                    "end_date": course.end_date,
                    "provider_name": course.provider_name,
                    "city": course.city,
                    "state": course.state,
                    "url": course.url,
                    "first_seen": course.first_seen,
                    "last_seen": course.last_seen,
                }
                for course in courses
            ])
        
        return data
    
    def _export_json(self, data: Dict[str, pd.DataFrame], output_dir: Path, session_id: str) -> List[Path]:
        """Export data to JSON format."""
        files = []
        
        for entity_type, df in data.items():
            output_file = output_dir / f"{entity_type}_{session_id}.json"
            
            # Convert DataFrame to JSON with proper date handling
            df_dict = df.to_dict(orient="records")
            
            # Convert dates to strings
            for record in df_dict:
                for key, value in record.items():
                    if pd.api.types.is_datetime64_any_dtype(type(value)):
                        record[key] = value.isoformat() if pd.notna(value) else None
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(df_dict, f, indent=2, ensure_ascii=False)
            
            files.append(output_file)
            logger.info(f"Exported {len(df)} {entity_type} to {output_file}")
        
        return files
    
    def _export_csv(self, data: Dict[str, pd.DataFrame], output_dir: Path, session_id: str) -> List[Path]:
        """Export data to CSV format."""
        files = []
        
        for entity_type, df in data.items():
            output_file = output_dir / f"{entity_type}_{session_id}.csv"
            df.to_csv(output_file, index=False, encoding="utf-8")
            files.append(output_file)
            logger.info(f"Exported {len(df)} {entity_type} to {output_file}")
        
        return files
    
    def _export_parquet(self, data: Dict[str, pd.DataFrame], output_dir: Path, session_id: str) -> List[Path]:
        """Export data to Parquet format."""
        files = []
        
        for entity_type, df in data.items():
            output_file = output_dir / f"{entity_type}_{session_id}.parquet"
            df.to_parquet(output_file, index=False, engine="pyarrow")
            files.append(output_file)
            logger.info(f"Exported {len(df)} {entity_type} to {output_file}")
        
        return files
    
    def _export_excel(self, data: Dict[str, pd.DataFrame], output_dir: Path, session_id: str) -> List[Path]:
        """Export data to Excel format."""
        output_file = output_dir / f"renec_harvest_{session_id}.xlsx"
        
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            for entity_type, df in data.items():
                # Truncate sheet name if too long
                sheet_name = entity_type[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                logger.info(f"Added {len(df)} {entity_type} to Excel file")
        
        return [output_file]