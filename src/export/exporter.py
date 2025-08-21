"""
Data exporter for various formats.
"""
import csv
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import zipfile

from sqlalchemy import select
from sqlalchemy.orm import Session
import pandas as pd

from src.models import get_session
from src.models.ec_standard import ECStandard
from src.models.certificador import Certificador


logger = logging.getLogger(__name__)


class DataExporter:
    """Export RENEC data to various formats."""
    
    def __init__(self):
        """Initialize exporter."""
        self.export_stats = {
            'total_records': 0,
            'files_created': [],
            'start_time': datetime.now()
        }
    
    def export_to_json(self, 
                      output_path: str,
                      entity_types: Optional[List[str]] = None,
                      filters: Optional[Dict[str, Any]] = None,
                      pretty: bool = True) -> str:
        """
        Export data to JSON format.
        
        Args:
            output_path: Path for output file
            entity_types: Entity types to export (default: all)
            filters: Optional filters to apply
            pretty: Pretty print JSON
            
        Returns:
            Path to exported file
        """
        if not entity_types:
            entity_types = ['ec_standards', 'certificadores']
        
        logger.info(f"Exporting to JSON: {entity_types}")
        
        export_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'version': '1.0',
                'source': 'RENEC Harvester',
                'filters': filters or {}
            },
            'data': {}
        }
        
        # Export each entity type
        for entity_type in entity_types:
            if entity_type == 'ec_standards':
                export_data['data']['ec_standards'] = self._export_ec_standards(filters)
            elif entity_type == 'certificadores':
                export_data['data']['certificadores'] = self._export_certificadores(filters)
        
        # Update stats
        self.export_stats['total_records'] = sum(
            len(records) for records in export_data['data'].values()
        )
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            else:
                json.dump(export_data, f, ensure_ascii=False, default=str)
        
        self.export_stats['files_created'].append(str(output_path))
        logger.info(f"Exported {self.export_stats['total_records']} records to {output_path}")
        
        return str(output_path)
    
    def export_to_csv(self,
                     output_dir: str,
                     entity_types: Optional[List[str]] = None,
                     filters: Optional[Dict[str, Any]] = None,
                     separate_files: bool = True) -> List[str]:
        """
        Export data to CSV format.
        
        Args:
            output_dir: Directory for output files
            entity_types: Entity types to export
            filters: Optional filters
            separate_files: Create separate file per entity type
            
        Returns:
            List of created file paths
        """
        if not entity_types:
            entity_types = ['ec_standards', 'certificadores']
        
        logger.info(f"Exporting to CSV: {entity_types}")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        created_files = []
        
        for entity_type in entity_types:
            if entity_type == 'ec_standards':
                data = self._export_ec_standards(filters)
                if data:
                    file_path = output_dir / "ec_standards.csv"
                    self._write_ec_standards_csv(data, file_path)
                    created_files.append(str(file_path))
            
            elif entity_type == 'certificadores':
                data = self._export_certificadores(filters)
                if data:
                    file_path = output_dir / "certificadores.csv"
                    self._write_certificadores_csv(data, file_path)
                    created_files.append(str(file_path))
        
        self.export_stats['files_created'].extend(created_files)
        logger.info(f"Created {len(created_files)} CSV files")
        
        return created_files
    
    def export_to_excel(self,
                       output_path: str,
                       entity_types: Optional[List[str]] = None,
                       filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Export data to Excel format with multiple sheets.
        
        Args:
            output_path: Path for output file
            entity_types: Entity types to export
            filters: Optional filters
            
        Returns:
            Path to exported file
        """
        if not entity_types:
            entity_types = ['ec_standards', 'certificadores']
        
        logger.info(f"Exporting to Excel: {entity_types}")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Add metadata sheet
            metadata = pd.DataFrame([{
                'Exported At': datetime.now().isoformat(),
                'Version': '1.0',
                'Source': 'RENEC Harvester'
            }])
            metadata.to_excel(writer, sheet_name='Metadata', index=False)
            
            # Export each entity type to separate sheet
            for entity_type in entity_types:
                if entity_type == 'ec_standards':
                    data = self._export_ec_standards(filters)
                    if data:
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name='EC Standards', index=False)
                        self.export_stats['total_records'] += len(data)
                
                elif entity_type == 'certificadores':
                    data = self._export_certificadores(filters)
                    if data:
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name='Certificadores', index=False)
                        self.export_stats['total_records'] += len(data)
        
        self.export_stats['files_created'].append(str(output_path))
        logger.info(f"Exported to Excel: {output_path}")
        
        return str(output_path)
    
    def export_bundle(self,
                     output_path: str,
                     formats: List[str] = None,
                     entity_types: Optional[List[str]] = None,
                     filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Export data bundle with multiple formats in a ZIP file.
        
        Args:
            output_path: Path for output ZIP file
            formats: Export formats (json, csv, excel)
            entity_types: Entity types to export
            filters: Optional filters
            
        Returns:
            Path to ZIP file
        """
        if not formats:
            formats = ['json', 'csv', 'excel']
        
        logger.info(f"Creating export bundle with formats: {formats}")
        
        # Create temporary directory for exports
        temp_dir = Path(output_path).parent / f"export_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        bundle_files = []
        
        try:
            # Export to each format
            if 'json' in formats:
                json_path = temp_dir / "data.json"
                self.export_to_json(str(json_path), entity_types, filters)
                bundle_files.append(json_path)
            
            if 'csv' in formats:
                csv_dir = temp_dir / "csv"
                csv_files = self.export_to_csv(str(csv_dir), entity_types, filters)
                bundle_files.extend([Path(f) for f in csv_files])
            
            if 'excel' in formats:
                excel_path = temp_dir / "data.xlsx"
                self.export_to_excel(str(excel_path), entity_types, filters)
                bundle_files.append(excel_path)
            
            # Add specialized JSON exports
            if 'json' in formats:
                # Graph format
                graph_path = temp_dir / "graph.json"
                self.export_graph_json(str(graph_path), entity_types, filters)
                bundle_files.append(graph_path)
                
                # Denormalized format
                denorm_path = temp_dir / "denormalized.json"
                self.export_denormalized_json(str(denorm_path), entity_types, filters)
                bundle_files.append(denorm_path)
            
            # Create ZIP file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in bundle_files:
                    if file_path.exists():
                        arcname = file_path.relative_to(temp_dir)
                        zf.write(file_path, arcname)
            
            logger.info(f"Created export bundle: {output_path}")
            return str(output_path)
            
        finally:
            # Cleanup temp directory
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def export_graph_json(self,
                         output_path: str,
                         entity_types: Optional[List[str]] = None,
                         filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Export data in graph format (nodes and edges).
        
        Args:
            output_path: Path for output file
            entity_types: Entity types to include
            filters: Optional filters
            
        Returns:
            Path to exported file
        """
        logger.info("Exporting to graph JSON format")
        
        graph_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'version': '1.0',
                'format': 'graph',
                'source': 'RENEC Harvester'
            },
            'nodes': [],
            'edges': []
        }
        
        with get_session() as session:
            # Export EC Standards as nodes
            if not entity_types or 'ec_standards' in entity_types:
                for ec in session.query(ECStandard).all():
                    graph_data['nodes'].append({
                        'id': f'ec_{ec.ec_clave}',
                        'type': 'ec_standard',
                        'label': ec.ec_clave,
                        'properties': {
                            'titulo': ec.titulo,
                            'vigente': ec.vigente,
                            'sector': ec.sector,
                            'nivel': ec.nivel
                        }
                    })
            
            # Export Certificadores as nodes
            if not entity_types or 'certificadores' in entity_types:
                for cert in session.query(Certificador).all():
                    graph_data['nodes'].append({
                        'id': f'cert_{cert.cert_id}',
                        'type': 'certificador',
                        'label': cert.cert_id,
                        'properties': {
                            'nombre_legal': cert.nombre_legal,
                            'tipo': cert.tipo,
                            'estado': cert.estado,
                            'estatus': cert.estatus
                        }
                    })
            
            # Export relationships as edges
            from src.models.relations import ECEEC, CentroEC, ECSector
            
            # ECE-EC relationships
            for rel in session.query(ECEEC).all():
                graph_data['edges'].append({
                    'id': f'rel_ece_ec_{rel.id}',
                    'source': f'cert_{rel.cert_id}',
                    'target': f'ec_{rel.ec_clave}',
                    'type': 'accredits',
                    'properties': {
                        'since': rel.acreditado_desde.isoformat() if rel.acreditado_desde else None
                    }
                })
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Exported graph format to {output_path}")
        return str(output_path)
    
    def export_denormalized_json(self,
                                output_path: str,
                                entity_types: Optional[List[str]] = None,
                                filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Export denormalized data with embedded relationships.
        
        Args:
            output_path: Path for output file
            entity_types: Entity types to include
            filters: Optional filters
            
        Returns:
            Path to exported file
        """
        logger.info("Exporting to denormalized JSON format")
        
        denorm_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'version': '1.0',
                'format': 'denormalized',
                'source': 'RENEC Harvester'
            },
            'data': {
                'ec_standards_with_relations': [],
                'certificadores_with_relations': []
            }
        }
        
        with get_session() as session:
            # Export EC Standards with all relationships
            if not entity_types or 'ec_standards' in entity_types:
                for ec in session.query(ECStandard).all():
                    ec_data = {
                        'ec_clave': ec.ec_clave,
                        'titulo': ec.titulo,
                        'version': ec.version,
                        'vigente': ec.vigente,
                        'sector': ec.sector,
                        'certificadores': [],
                        'centros': []
                    }
                    
                    # Get certificadores that accredit this standard
                    from src.models.relations import ECEEC
                    for rel in session.query(ECEEC).filter(ECEEC.ec_clave == ec.ec_clave).all():
                        cert = session.query(Certificador).filter(
                            Certificador.cert_id == rel.cert_id
                        ).first()
                        if cert:
                            ec_data['certificadores'].append({
                                'cert_id': cert.cert_id,
                                'nombre_legal': cert.nombre_legal,
                                'tipo': cert.tipo,
                                'estado': cert.estado
                            })
                    
                    denorm_data['data']['ec_standards_with_relations'].append(ec_data)
            
            # Export Certificadores with their standards
            if not entity_types or 'certificadores' in entity_types:
                for cert in session.query(Certificador).all():
                    cert_data = {
                        'cert_id': cert.cert_id,
                        'tipo': cert.tipo,
                        'nombre_legal': cert.nombre_legal,
                        'estado': cert.estado,
                        'estado_inegi': cert.estado_inegi,
                        'ec_standards': []
                    }
                    
                    # Get EC standards this certificador accredits
                    if cert.estandares_acreditados:
                        for ec_code in cert.estandares_acreditados:
                            ec = session.query(ECStandard).filter(
                                ECStandard.ec_clave == ec_code
                            ).first()
                            if ec:
                                cert_data['ec_standards'].append({
                                    'ec_clave': ec.ec_clave,
                                    'titulo': ec.titulo,
                                    'vigente': ec.vigente
                                })
                    
                    denorm_data['data']['certificadores_with_relations'].append(cert_data)
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(denorm_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Exported denormalized format to {output_path}")
        return str(output_path)
    
    def _export_ec_standards(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Export EC standards data."""
        records = []
        
        with get_session() as session:
            query = select(ECStandard)
            
            # Apply filters
            if filters:
                if 'vigente' in filters:
                    query = query.where(ECStandard.vigente == filters['vigente'])
                if 'sector_id' in filters:
                    query = query.where(ECStandard.sector_id == filters['sector_id'])
            
            for ec in session.execute(query).scalars():
                records.append({
                    'ec_clave': ec.ec_clave,
                    'titulo': ec.titulo,
                    'version': ec.version,
                    'vigente': ec.vigente,
                    'sector': ec.sector,
                    'sector_id': ec.sector_id,
                    'comite': ec.comite,
                    'comite_id': ec.comite_id,
                    'descripcion': ec.descripcion,
                    'competencias': json.dumps(ec.competencias, ensure_ascii=False) if ec.competencias else None,
                    'nivel': ec.nivel,
                    'duracion_horas': ec.duracion_horas,
                    'tipo_norma': ec.tipo_norma,
                    'fecha_publicacion': ec.fecha_publicacion.isoformat() if ec.fecha_publicacion else None,
                    'fecha_vigencia': ec.fecha_vigencia.isoformat() if ec.fecha_vigencia else None,
                    'perfil_evaluador': ec.perfil_evaluador,
                    'criterios_evaluacion': json.dumps(ec.criterios_evaluacion, ensure_ascii=False) if ec.criterios_evaluacion else None,
                    'renec_url': ec.renec_url,
                    'first_seen': ec.first_seen.isoformat() if ec.first_seen else None,
                    'last_seen': ec.last_seen.isoformat() if ec.last_seen else None
                })
        
        return records
    
    def _export_certificadores(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Export certificadores data."""
        records = []
        
        with get_session() as session:
            query = select(Certificador)
            
            # Apply filters
            if filters:
                if 'tipo' in filters:
                    query = query.where(Certificador.tipo == filters['tipo'])
                if 'estado_inegi' in filters:
                    query = query.where(Certificador.estado_inegi == filters['estado_inegi'])
                if 'estatus' in filters:
                    query = query.where(Certificador.estatus == filters['estatus'])
            
            for cert in session.execute(query).scalars():
                records.append({
                    'cert_id': cert.cert_id,
                    'tipo': cert.tipo,
                    'nombre_legal': cert.nombre_legal,
                    'siglas': cert.siglas,
                    'estatus': cert.estatus,
                    'domicilio_texto': cert.domicilio_texto,
                    'estado': cert.estado,
                    'estado_inegi': cert.estado_inegi,
                    'municipio': cert.municipio,
                    'cp': cert.cp,
                    'telefono': cert.telefono,
                    'correo': cert.correo,
                    'sitio_web': cert.sitio_web,
                    'representante_legal': cert.representante_legal,
                    'fecha_acreditacion': cert.fecha_acreditacion.isoformat() if cert.fecha_acreditacion else None,
                    'estandares_acreditados': json.dumps(cert.estandares_acreditados, ensure_ascii=False) if cert.estandares_acreditados else None,
                    'contactos_adicionales': json.dumps(cert.contactos_adicionales, ensure_ascii=False) if cert.contactos_adicionales else None,
                    'src_url': cert.src_url,
                    'first_seen': cert.first_seen.isoformat() if cert.first_seen else None,
                    'last_seen': cert.last_seen.isoformat() if cert.last_seen else None
                })
        
        return records
    
    def _write_ec_standards_csv(self, data: List[Dict[str, Any]], file_path: Path):
        """Write EC standards to CSV."""
        if not data:
            return
        
        fieldnames = [
            'ec_clave', 'titulo', 'version', 'vigente', 'sector', 'sector_id',
            'comite', 'comite_id', 'descripcion', 'competencias', 'nivel',
            'duracion_horas', 'tipo_norma', 'fecha_publicacion', 'fecha_vigencia',
            'perfil_evaluador', 'criterios_evaluacion', 'renec_url',
            'first_seen', 'last_seen'
        ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        self.export_stats['total_records'] += len(data)
    
    def _write_certificadores_csv(self, data: List[Dict[str, Any]], file_path: Path):
        """Write certificadores to CSV."""
        if not data:
            return
        
        fieldnames = [
            'cert_id', 'tipo', 'nombre_legal', 'siglas', 'estatus',
            'domicilio_texto', 'estado', 'estado_inegi', 'municipio',
            'cp', 'telefono', 'correo', 'sitio_web', 'representante_legal',
            'fecha_acreditacion', 'estandares_acreditados', 'contactos_adicionales',
            'src_url', 'first_seen', 'last_seen'
        ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        self.export_stats['total_records'] += len(data)
    
    def get_export_summary(self) -> Dict[str, Any]:
        """Get export operation summary."""
        runtime = (datetime.now() - self.export_stats['start_time']).total_seconds()
        
        return {
            'total_records': self.export_stats['total_records'],
            'files_created': self.export_stats['files_created'],
            'runtime_seconds': runtime,
            'records_per_second': self.export_stats['total_records'] / runtime if runtime > 0 else 0
        }