"""
Cross-entity search API endpoints.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from src.models import get_session
from src.models import ECStandardV2 as ECStandard
from src.models import CertificadorV2 as Certificador
from src.models.centro import Centro
from src.models.sector import Sector
from src.models.comite import Comite


router = APIRouter()


@router.get("/search")
async def search_all(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types to search"),
    limit: int = Query(10, ge=1, le=50, description="Max results per entity type"),
    db: Session = Depends(get_session)
):
    """
    Search across all entity types.
    
    - **q**: Search query (searches in IDs, names, titles)
    - **entity_types**: Filter by entity types (ec_standards, certificadores, centros, sectores, comites)
    - **limit**: Maximum results per entity type
    """
    search_term = f"%{q}%"
    results = {}
    
    # Parse entity types
    if entity_types:
        types_to_search = [t.strip() for t in entity_types.split(",")]
    else:
        types_to_search = ["ec_standards", "certificadores", "centros", "sectores", "comites"]
    
    # Search EC Standards
    if "ec_standards" in types_to_search:
        ec_query = db.query(ECStandard).filter(
            or_(
                ECStandard.ec_clave.ilike(search_term),
                ECStandard.titulo.ilike(search_term)
            )
        ).limit(limit)
        
        ec_results = [
            {
                'ec_clave': ec.ec_clave,
                'titulo': ec.titulo,
                'vigente': ec.vigente,
                'sector': ec.sector,
                'nivel': ec.nivel
            }
            for ec in ec_query.all()
        ]
        
        if ec_results:
            results['ec_standards'] = {
                'count': len(ec_results),
                'items': ec_results
            }
    
    # Search Certificadores
    if "certificadores" in types_to_search:
        cert_query = db.query(Certificador).filter(
            or_(
                Certificador.cert_id.ilike(search_term),
                Certificador.nombre_legal.ilike(search_term),
                Certificador.siglas.ilike(search_term)
            )
        ).limit(limit)
        
        cert_results = [
            {
                'cert_id': cert.cert_id,
                'tipo': cert.tipo,
                'nombre_legal': cert.nombre_legal,
                'siglas': cert.siglas,
                'estado': cert.estado,
                'estatus': cert.estatus
            }
            for cert in cert_query.all()
        ]
        
        if cert_results:
            results['certificadores'] = {
                'count': len(cert_results),
                'items': cert_results
            }
    
    # Search Centros
    if "centros" in types_to_search:
        centro_query = db.query(Centro).filter(
            or_(
                Centro.centro_id.ilike(search_term),
                Centro.nombre.ilike(search_term)
            )
        ).limit(limit)
        
        centro_results = [
            {
                'centro_id': centro.centro_id,
                'nombre': centro.nombre,
                'estado': centro.estado,
                'municipio': centro.municipio
            }
            for centro in centro_query.all()
        ]
        
        if centro_results:
            results['centros'] = {
                'count': len(centro_results),
                'items': centro_results
            }
    
    # Search Sectores
    if "sectores" in types_to_search:
        sector_query = db.query(Sector).filter(
            Sector.nombre.ilike(search_term)
        ).limit(limit)
        
        sector_results = [
            {
                'sector_id': sector.sector_id,
                'nombre': sector.nombre
            }
            for sector in sector_query.all()
        ]
        
        if sector_results:
            results['sectores'] = {
                'count': len(sector_results),
                'items': sector_results
            }
    
    # Search Comités
    if "comites" in types_to_search:
        comite_query = db.query(Comite).filter(
            Comite.nombre.ilike(search_term)
        ).limit(limit)
        
        comite_results = [
            {
                'comite_id': comite.comite_id,
                'nombre': comite.nombre,
                'sector_id': comite.sector_id
            }
            for comite in comite_query.all()
        ]
        
        if comite_results:
            results['comites'] = {
                'count': len(comite_results),
                'items': comite_results
            }
    
    # Calculate total results
    total_results = sum(r['count'] for r in results.values())
    
    return {
        'query': q,
        'total_results': total_results,
        'results': results
    }


@router.get("/search/suggest")
async def search_suggestions(
    q: str = Query(..., min_length=2, max_length=50, description="Partial query for suggestions"),
    entity_type: str = Query(..., description="Entity type (ec_standards, certificadores, centros)"),
    limit: int = Query(5, ge=1, le=20, description="Max suggestions"),
    db: Session = Depends(get_session)
):
    """
    Get search suggestions for autocomplete.
    
    - **q**: Partial query (minimum 2 characters)
    - **entity_type**: Type of entity to search
    - **limit**: Maximum number of suggestions
    """
    search_term = f"{q}%"  # Prefix match for suggestions
    suggestions = []
    
    if entity_type == "ec_standards":
        results = db.query(
            ECStandard.ec_clave,
            ECStandard.titulo
        ).filter(
            or_(
                ECStandard.ec_clave.ilike(search_term),
                ECStandard.titulo.ilike(f"%{q}%")
            )
        ).limit(limit).all()
        
        suggestions = [
            {
                'value': r.ec_clave,
                'label': f"{r.ec_clave} - {r.titulo[:50]}..."
            }
            for r in results
        ]
    
    elif entity_type == "certificadores":
        results = db.query(
            Certificador.cert_id,
            Certificador.nombre_legal,
            Certificador.siglas
        ).filter(
            or_(
                Certificador.cert_id.ilike(search_term),
                Certificador.nombre_legal.ilike(f"%{q}%"),
                Certificador.siglas.ilike(search_term)
            )
        ).limit(limit).all()
        
        suggestions = [
            {
                'value': r.cert_id,
                'label': f"{r.cert_id} - {r.nombre_legal}" + (f" ({r.siglas})" if r.siglas else "")
            }
            for r in results
        ]
    
    elif entity_type == "centros":
        results = db.query(
            Centro.centro_id,
            Centro.nombre
        ).filter(
            or_(
                Centro.centro_id.ilike(search_term),
                Centro.nombre.ilike(f"%{q}%")
            )
        ).limit(limit).all()
        
        suggestions = [
            {
                'value': r.centro_id,
                'label': f"{r.centro_id} - {r.nombre}"
            }
            for r in results
        ]
    
    return {
        'query': q,
        'entity_type': entity_type,
        'suggestions': suggestions
    }


@router.get("/search/by-location")
async def search_by_location(
    estado_inegi: str = Query(..., description="INEGI state code"),
    municipio: Optional[str] = Query(None, description="Municipality name"),
    entity_types: Optional[str] = Query("certificadores,centros", description="Entity types to search"),
    db: Session = Depends(get_session)
):
    """
    Search entities by location (state and municipality).
    
    - **estado_inegi**: INEGI state code (e.g., 09 for CDMX)
    - **municipio**: Municipality name (optional)
    - **entity_types**: Comma-separated entity types (certificadores, centros)
    """
    results = {}
    types_to_search = [t.strip() for t in entity_types.split(",")]
    
    # Search Certificadores
    if "certificadores" in types_to_search:
        cert_query = db.query(Certificador).filter(
            Certificador.estado_inegi == estado_inegi
        )
        
        if municipio:
            cert_query = cert_query.filter(
                Certificador.municipio.ilike(f"%{municipio}%")
            )
        
        certificadores = cert_query.all()
        
        results['certificadores'] = {
            'count': len(certificadores),
            'by_tipo': {
                'ECE': len([c for c in certificadores if c.tipo == 'ECE']),
                'OC': len([c for c in certificadores if c.tipo == 'OC'])
            },
            'items': [
                {
                    'cert_id': c.cert_id,
                    'tipo': c.tipo,
                    'nombre_legal': c.nombre_legal,
                    'municipio': c.municipio,
                    'telefono': c.telefono,
                    'correo': c.correo
                }
                for c in certificadores[:20]  # Limit to 20 items
            ]
        }
    
    # Search Centros
    if "centros" in types_to_search:
        centro_query = db.query(Centro).filter(
            Centro.estado_inegi == estado_inegi
        )
        
        if municipio:
            centro_query = centro_query.filter(
                Centro.municipio.ilike(f"%{municipio}%")
            )
        
        centros = centro_query.all()
        
        results['centros'] = {
            'count': len(centros),
            'items': [
                {
                    'centro_id': c.centro_id,
                    'nombre': c.nombre,
                    'municipio': c.municipio,
                    'telefono': c.telefono,
                    'correo': c.correo
                }
                for c in centros[:20]  # Limit to 20 items
            ]
        }
    
    # Get location name
    estado_nombre = "Unknown"
    if results:
        if 'certificadores' in results and results['certificadores']['items']:
            first_item = db.query(Certificador).filter(
                Certificador.estado_inegi == estado_inegi
            ).first()
            if first_item:
                estado_nombre = first_item.estado
        elif 'centros' in results and results['centros']['items']:
            first_item = db.query(Centro).filter(
                Centro.estado_inegi == estado_inegi
            ).first()
            if first_item:
                estado_nombre = first_item.estado
    
    return {
        'location': {
            'estado_inegi': estado_inegi,
            'estado_nombre': estado_nombre,
            'municipio': municipio
        },
        'results': results
    }


@router.get("/search/related/{entity_type}/{entity_id}")
async def search_related_entities(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_session)
):
    """
    Find entities related to a specific entity.
    
    - **entity_type**: Type of the source entity (ec_standard, certificador, centro)
    - **entity_id**: ID of the source entity
    """
    related = {}
    
    if entity_type == "ec_standard":
        # Verify EC exists
        ec = db.query(ECStandard).filter(ECStandard.ec_clave == entity_id).first()
        if not ec:
            return {'error': f'EC Standard {entity_id} not found'}
        
        related['ec_standard'] = {
            'ec_clave': ec.ec_clave,
            'titulo': ec.titulo,
            'vigente': ec.vigente
        }
        
        # Get related certificadores
        from src.models.relations import ECEEC
        ece_relations = db.query(ECEEC).filter(ECEEC.ec_clave == entity_id).all()
        cert_ids = [rel.cert_id for rel in ece_relations]
        
        if cert_ids:
            certificadores = db.query(Certificador).filter(
                Certificador.cert_id.in_(cert_ids)
            ).all()
            
            related['certificadores'] = {
                'count': len(certificadores),
                'items': [
                    {
                        'cert_id': c.cert_id,
                        'nombre_legal': c.nombre_legal,
                        'tipo': c.tipo,
                        'estado': c.estado
                    }
                    for c in certificadores
                ]
            }
        
        # Get related centros
        from src.models.relations import CentroEC
        centro_relations = db.query(CentroEC).filter(CentroEC.ec_clave == entity_id).all()
        centro_ids = [rel.centro_id for rel in centro_relations]
        
        if centro_ids:
            centros = db.query(Centro).filter(
                Centro.centro_id.in_(centro_ids)
            ).all()
            
            related['centros'] = {
                'count': len(centros),
                'items': [
                    {
                        'centro_id': c.centro_id,
                        'nombre': c.nombre,
                        'estado': c.estado,
                        'municipio': c.municipio
                    }
                    for c in centros
                ]
            }
        
        # Get sector and committee
        if ec.sector_id:
            sector = db.query(Sector).filter(Sector.sector_id == ec.sector_id).first()
            if sector:
                related['sector'] = {
                    'sector_id': sector.sector_id,
                    'nombre': sector.nombre
                }
        
        if ec.comite_id:
            comite = db.query(Comite).filter(Comite.comite_id == ec.comite_id).first()
            if comite:
                related['comite'] = {
                    'comite_id': comite.comite_id,
                    'nombre': comite.nombre
                }
    
    elif entity_type == "certificador":
        # Similar logic for certificador relationships
        cert = db.query(Certificador).filter(Certificador.cert_id == entity_id).first()
        if not cert:
            return {'error': f'Certificador {entity_id} not found'}
        
        related['certificador'] = {
            'cert_id': cert.cert_id,
            'nombre_legal': cert.nombre_legal,
            'tipo': cert.tipo
        }
        
        # Get EC standards if ECE type
        if cert.tipo == 'ECE':
            from src.models.relations import ECEEC
            ece_relations = db.query(ECEEC).filter(ECEEC.cert_id == entity_id).all()
            ec_claves = [rel.ec_clave for rel in ece_relations]
            
            if ec_claves:
                standards = db.query(ECStandard).filter(
                    ECStandard.ec_clave.in_(ec_claves)
                ).all()
                
                related['ec_standards'] = {
                    'count': len(standards),
                    'items': [
                        {
                            'ec_clave': ec.ec_clave,
                            'titulo': ec.titulo,
                            'vigente': ec.vigente
                        }
                        for ec in standards
                    ]
                }
    
    return related