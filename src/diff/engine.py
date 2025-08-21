"""
Diff engine for detecting changes between harvests.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict
import hashlib
import json

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.models import get_session
from src.models.ec_standard import ECStandard
from src.models.certificador import Certificador


logger = logging.getLogger(__name__)


class DiffEngine:
    """Engine for detecting changes between data snapshots."""
    
    def __init__(self):
        """Initialize diff engine."""
        self.stats = defaultdict(int)
        self.changes = []
        
    def compare_harvests(self, 
                        timestamp1: datetime, 
                        timestamp2: datetime,
                        entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare two harvest snapshots.
        
        Args:
            timestamp1: Earlier timestamp
            timestamp2: Later timestamp
            entity_types: Specific entities to compare (default: all)
            
        Returns:
            Diff report with changes
        """
        if not entity_types:
            entity_types = ['ec_standards', 'certificadores']
        
        logger.info(f"Comparing harvests between {timestamp1} and {timestamp2}")
        
        diff_report = {
            'timestamp1': timestamp1.isoformat(),
            'timestamp2': timestamp2.isoformat(),
            'duration': (timestamp2 - timestamp1).total_seconds(),
            'changes_by_type': {},
            'summary': {},
            'generated_at': datetime.now().isoformat()
        }
        
        # Compare each entity type
        for entity_type in entity_types:
            if entity_type == 'ec_standards':
                changes = self._compare_ec_standards(timestamp1, timestamp2)
            elif entity_type == 'certificadores':
                changes = self._compare_certificadores(timestamp1, timestamp2)
            else:
                logger.warning(f"Unknown entity type: {entity_type}")
                continue
            
            diff_report['changes_by_type'][entity_type] = changes
        
        # Generate summary
        diff_report['summary'] = self._generate_summary(diff_report['changes_by_type'])
        
        return diff_report
    
    def _compare_ec_standards(self, time1: datetime, time2: datetime) -> Dict[str, Any]:
        """Compare EC standards between two timestamps."""
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'stats': defaultdict(int)
        }
        
        with get_session() as session:
            # Get standards at each timestamp
            standards1 = self._get_ec_standards_at_time(session, time1)
            standards2 = self._get_ec_standards_at_time(session, time2)
            
            keys1 = set(standards1.keys())
            keys2 = set(standards2.keys())
            
            # Find additions
            for key in keys2 - keys1:
                changes['added'].append({
                    'ec_clave': key,
                    'data': standards2[key]
                })
                changes['stats']['added'] += 1
            
            # Find removals
            for key in keys1 - keys2:
                changes['removed'].append({
                    'ec_clave': key,
                    'data': standards1[key]
                })
                changes['stats']['removed'] += 1
            
            # Find modifications
            for key in keys1 & keys2:
                diff = self._compare_ec_records(standards1[key], standards2[key])
                if diff['has_changes']:
                    changes['modified'].append({
                        'ec_clave': key,
                        'changes': diff['changes'],
                        'before': standards1[key],
                        'after': standards2[key]
                    })
                    changes['stats']['modified'] += 1
                    
                    # Track field-level changes
                    for field in diff['changed_fields']:
                        changes['stats'][f'field_{field}'] = changes['stats'].get(f'field_{field}', 0) + 1
        
        changes['stats']['total_before'] = len(keys1)
        changes['stats']['total_after'] = len(keys2)
        changes['stats']['unchanged'] = len(keys1 & keys2) - changes['stats']['modified']
        
        return changes
    
    def _compare_certificadores(self, time1: datetime, time2: datetime) -> Dict[str, Any]:
        """Compare certificadores between two timestamps."""
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'stats': defaultdict(int)
        }
        
        with get_session() as session:
            # Get certificadores at each timestamp
            certs1 = self._get_certificadores_at_time(session, time1)
            certs2 = self._get_certificadores_at_time(session, time2)
            
            keys1 = set(certs1.keys())
            keys2 = set(certs2.keys())
            
            # Find additions
            for key in keys2 - keys1:
                changes['added'].append({
                    'cert_id': key,
                    'data': certs2[key]
                })
                changes['stats']['added'] += 1
            
            # Find removals
            for key in keys1 - keys2:
                changes['removed'].append({
                    'cert_id': key,
                    'data': certs1[key]
                })
                changes['stats']['removed'] += 1
            
            # Find modifications
            for key in keys1 & keys2:
                diff = self._compare_cert_records(certs1[key], certs2[key])
                if diff['has_changes']:
                    changes['modified'].append({
                        'cert_id': key,
                        'changes': diff['changes'],
                        'before': certs1[key],
                        'after': certs2[key]
                    })
                    changes['stats']['modified'] += 1
                    
                    # Track specific changes
                    if 'estatus' in diff['changed_fields']:
                        changes['stats']['status_changes'] += 1
                    if 'estandares_acreditados' in diff['changed_fields']:
                        changes['stats']['accreditation_changes'] += 1
        
        changes['stats']['total_before'] = len(keys1)
        changes['stats']['total_after'] = len(keys2)
        changes['stats']['unchanged'] = len(keys1 & keys2) - changes['stats']['modified']
        
        # Track by type
        for cert_data in certs2.values():
            tipo = cert_data.get('tipo', 'UNKNOWN')
            changes['stats'][f'type_{tipo}'] = changes['stats'].get(f'type_{tipo}', 0) + 1
        
        return changes
    
    def _get_ec_standards_at_time(self, session: Session, timestamp: datetime) -> Dict[str, Dict]:
        """Get EC standards snapshot at specific time."""
        standards = {}
        
        # Query standards that existed at the given timestamp
        query = select(ECStandard).where(
            and_(
                ECStandard.first_seen <= timestamp,
                ECStandard.last_seen >= timestamp
            )
        )
        
        for ec in session.execute(query).scalars():
            standards[ec.ec_clave] = {
                'titulo': ec.titulo,
                'version': ec.version,
                'vigente': ec.vigente,
                'sector': ec.sector,
                'sector_id': ec.sector_id,
                'comite': ec.comite,
                'comite_id': ec.comite_id,
                'nivel': ec.nivel,
                'duracion_horas': ec.duracion_horas,
                'tipo_norma': ec.tipo_norma,
                'fecha_publicacion': ec.fecha_publicacion.isoformat() if ec.fecha_publicacion else None,
                'fecha_vigencia': ec.fecha_vigencia.isoformat() if ec.fecha_vigencia else None,
                'content_hash': ec.content_hash
            }
        
        return standards
    
    def _get_certificadores_at_time(self, session: Session, timestamp: datetime) -> Dict[str, Dict]:
        """Get certificadores snapshot at specific time."""
        certificadores = {}
        
        query = select(Certificador).where(
            and_(
                Certificador.first_seen <= timestamp,
                Certificador.last_seen >= timestamp
            )
        )
        
        for cert in session.execute(query).scalars():
            certificadores[cert.cert_id] = {
                'tipo': cert.tipo,
                'nombre_legal': cert.nombre_legal,
                'siglas': cert.siglas,
                'estatus': cert.estatus,
                'estado': cert.estado,
                'estado_inegi': cert.estado_inegi,
                'municipio': cert.municipio,
                'telefono': cert.telefono,
                'correo': cert.correo,
                'sitio_web': cert.sitio_web,
                'representante_legal': cert.representante_legal,
                'fecha_acreditacion': cert.fecha_acreditacion.isoformat() if cert.fecha_acreditacion else None,
                'estandares_acreditados': cert.estandares_acreditados,
                'row_hash': cert.row_hash
            }
        
        return certificadores
    
    def _compare_ec_records(self, before: Dict, after: Dict) -> Dict[str, Any]:
        """Compare two EC standard records."""
        # Quick check using content hash
        if before.get('content_hash') == after.get('content_hash'):
            return {'has_changes': False, 'changes': {}, 'changed_fields': []}
        
        changes = {}
        changed_fields = []
        
        # Compare each field
        fields_to_compare = [
            'titulo', 'version', 'vigente', 'sector', 'sector_id',
            'comite', 'comite_id', 'nivel', 'duracion_horas',
            'tipo_norma', 'fecha_publicacion', 'fecha_vigencia'
        ]
        
        for field in fields_to_compare:
            if before.get(field) != after.get(field):
                changes[field] = {
                    'before': before.get(field),
                    'after': after.get(field)
                }
                changed_fields.append(field)
        
        return {
            'has_changes': len(changes) > 0,
            'changes': changes,
            'changed_fields': changed_fields
        }
    
    def _compare_cert_records(self, before: Dict, after: Dict) -> Dict[str, Any]:
        """Compare two certificador records."""
        # Quick check using row hash
        if before.get('row_hash') == after.get('row_hash'):
            return {'has_changes': False, 'changes': {}, 'changed_fields': []}
        
        changes = {}
        changed_fields = []
        
        # Compare each field
        fields_to_compare = [
            'nombre_legal', 'siglas', 'estatus', 'estado', 'estado_inegi',
            'municipio', 'telefono', 'correo', 'sitio_web',
            'representante_legal', 'fecha_acreditacion'
        ]
        
        for field in fields_to_compare:
            if before.get(field) != after.get(field):
                changes[field] = {
                    'before': before.get(field),
                    'after': after.get(field)
                }
                changed_fields.append(field)
        
        # Special handling for standards list
        before_standards = set(before.get('estandares_acreditados', []))
        after_standards = set(after.get('estandares_acreditados', []))
        
        if before_standards != after_standards:
            changes['estandares_acreditados'] = {
                'added': list(after_standards - before_standards),
                'removed': list(before_standards - after_standards),
                'before_count': len(before_standards),
                'after_count': len(after_standards)
            }
            changed_fields.append('estandares_acreditados')
        
        return {
            'has_changes': len(changes) > 0,
            'changes': changes,
            'changed_fields': changed_fields
        }
    
    def _generate_summary(self, changes_by_type: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate summary statistics from changes."""
        summary = {
            'total_changes': 0,
            'by_operation': defaultdict(int),
            'by_entity': {},
            'notable_changes': []
        }
        
        for entity_type, changes in changes_by_type.items():
            entity_summary = {
                'added': len(changes.get('added', [])),
                'removed': len(changes.get('removed', [])),
                'modified': len(changes.get('modified', [])),
                'total': 0
            }
            
            entity_summary['total'] = (
                entity_summary['added'] +
                entity_summary['removed'] +
                entity_summary['modified']
            )
            
            summary['by_entity'][entity_type] = entity_summary
            summary['total_changes'] += entity_summary['total']
            
            # Aggregate operations
            summary['by_operation']['added'] += entity_summary['added']
            summary['by_operation']['removed'] += entity_summary['removed']
            summary['by_operation']['modified'] += entity_summary['modified']
            
            # Identify notable changes
            if entity_type == 'certificadores' and 'stats' in changes:
                if changes['stats'].get('status_changes', 0) > 0:
                    summary['notable_changes'].append({
                        'type': 'status_changes',
                        'count': changes['stats']['status_changes'],
                        'description': f"{changes['stats']['status_changes']} certificadores changed status"
                    })
                
                if changes['stats'].get('accreditation_changes', 0) > 0:
                    summary['notable_changes'].append({
                        'type': 'accreditation_changes',
                        'count': changes['stats']['accreditation_changes'],
                        'description': f"{changes['stats']['accreditation_changes']} certificadores updated accredited standards"
                    })
        
        return summary
    
    def compare_with_baseline(self, 
                            current_data: List[Dict[str, Any]], 
                            baseline_data: List[Dict[str, Any]],
                            key_field: str) -> Dict[str, Any]:
        """
        Compare current data with baseline.
        
        Args:
            current_data: Current dataset
            baseline_data: Baseline dataset
            key_field: Field to use as unique key
            
        Returns:
            Comparison results
        """
        # Build lookup dictionaries
        current_map = {item[key_field]: item for item in current_data if key_field in item}
        baseline_map = {item[key_field]: item for item in baseline_data if key_field in item}
        
        current_keys = set(current_map.keys())
        baseline_keys = set(baseline_map.keys())
        
        # Find changes
        added = [current_map[k] for k in current_keys - baseline_keys]
        removed = [baseline_map[k] for k in baseline_keys - current_keys]
        
        modified = []
        for key in current_keys & baseline_keys:
            if self._compute_hash(current_map[key]) != self._compute_hash(baseline_map[key]):
                modified.append({
                    'key': key,
                    'before': baseline_map[key],
                    'after': current_map[key]
                })
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'summary': {
                'total_current': len(current_data),
                'total_baseline': len(baseline_data),
                'added_count': len(added),
                'removed_count': len(removed),
                'modified_count': len(modified),
                'unchanged_count': len(current_keys & baseline_keys) - len(modified)
            }
        }
    
    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute hash of dictionary for comparison."""
        # Sort keys for consistent hashing
        content = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()