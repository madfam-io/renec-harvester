"""
Centros (Evaluation Centers) API endpoints.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models import get_session
from src.models.centro import Centro
from src.api.models import PaginationParams, CentroResponse, CentroDetail


router = APIRouter()


@router.get("/centros", response_model=List[CentroResponse])
async def list_centros(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    estado_inegi: Optional[str] = Query(None, description="Filter by INEGI state code"),
    municipio: Optional[str] = Query(None, description="Filter by municipality"),
    search: Optional[str] = Query(None, description="Search in ID and name"),
    db: Session = Depends(get_session)
):
    """
    List evaluation centers with pagination and filtering.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **estado_inegi**: Filter by INEGI state code (e.g., 09 for CDMX)
    - **municipio**: Filter by municipality name
    - **search**: Search in center ID and name
    """
    query = select(Centro)
    
    # Apply filters
    if estado_inegi:
        query = query.where(Centro.estado_inegi == estado_inegi)
    
    if municipio:
        query = query.where(Centro.municipio.ilike(f"%{municipio}%"))
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Centro.centro_id.ilike(search_term)) |
            (Centro.nombre.ilike(search_term))
        )
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = db.execute(query)
    centros = result.scalars().all()
    
    return [
        CentroResponse(
            centro_id=centro.centro_id,
            nombre=centro.nombre,
            estado=centro.estado,
            estado_inegi=centro.estado_inegi,
            municipio=centro.municipio,
            domicilio=centro.domicilio,
            telefono=centro.telefono,
            correo=centro.correo,
            coordinador=centro.coordinador,
            last_seen=centro.last_seen
        )
        for centro in centros
    ]


@router.get("/centros/{centro_id}", response_model=CentroDetail)
async def get_centro(
    centro_id: str,
    db: Session = Depends(get_session)
):
    """
    Get detailed information for a specific evaluation center.
    
    - **centro_id**: The center ID (e.g., CE0001)
    """
    centro = db.query(Centro).filter(Centro.centro_id == centro_id).first()
    
    if not centro:
        raise HTTPException(status_code=404, detail=f"Centro {centro_id} not found")
    
    # Get EC standards this center can evaluate
    from src.models.relations import CentroEC
    from src.models import ECStandardV2 as ECStandard
    
    ec_standards = []
    centro_ec_relations = db.query(CentroEC).filter(CentroEC.centro_id == centro_id).all()
    
    for rel in centro_ec_relations:
        ec = db.query(ECStandard).filter(ECStandard.ec_clave == rel.ec_clave).first()
        if ec:
            ec_standards.append({
                'ec_clave': ec.ec_clave,
                'titulo': ec.titulo,
                'vigente': ec.vigente,
                'sector': ec.sector,
                'nivel': ec.nivel
            })
    
    # Get associated certificador if any
    certificador_info = None
    if centro.certificador_id:
        from src.models import CertificadorV2 as Certificador
        cert = db.query(Certificador).filter(Certificador.cert_id == centro.certificador_id).first()
        if cert:
            certificador_info = {
                'cert_id': cert.cert_id,
                'nombre_legal': cert.nombre_legal,
                'tipo': cert.tipo
            }
    
    return CentroDetail(
        centro_id=centro.centro_id,
        nombre=centro.nombre,
        estado=centro.estado,
        estado_inegi=centro.estado_inegi,
        municipio=centro.municipio,
        domicilio=centro.domicilio,
        telefono=centro.telefono,
        extension=centro.extension,
        correo=centro.correo,
        sitio_web=centro.sitio_web,
        coordinador=centro.coordinador,
        certificador_id=centro.certificador_id,
        src_url=centro.src_url,
        first_seen=centro.first_seen,
        last_seen=centro.last_seen,
        ec_standards=ec_standards,
        certificador=certificador_info
    )


@router.get("/centros/{centro_id}/ec-standards")
async def get_centro_standards(
    centro_id: str,
    vigente: Optional[bool] = Query(None, description="Filter by vigente status"),
    db: Session = Depends(get_session)
):
    """
    Get all EC standards that this center can evaluate.
    """
    # Verify centro exists
    centro = db.query(Centro).filter(Centro.centro_id == centro_id).first()
    if not centro:
        raise HTTPException(status_code=404, detail=f"Centro {centro_id} not found")
    
    from src.models.relations import CentroEC
    from src.models import ECStandardV2 as ECStandard
    
    query = db.query(ECStandard).join(
        CentroEC, CentroEC.ec_clave == ECStandard.ec_clave
    ).filter(CentroEC.centro_id == centro_id)
    
    if vigente is not None:
        query = query.filter(ECStandard.vigente == vigente)
    
    standards = query.all()
    
    return {
        'centro_id': centro_id,
        'nombre': centro.nombre,
        'total_standards': len(standards),
        'ec_standards': [
            {
                'ec_clave': ec.ec_clave,
                'titulo': ec.titulo,
                'version': ec.version,
                'vigente': ec.vigente,
                'sector': ec.sector,
                'nivel': ec.nivel,
                'duracion_horas': ec.duracion_horas
            }
            for ec in standards
        ]
    }


@router.get("/centros/by-state/{estado_inegi}")
async def get_centros_by_state(
    estado_inegi: str,
    db: Session = Depends(get_session)
):
    """
    Get all evaluation centers in a specific state.
    
    - **estado_inegi**: INEGI state code (e.g., 09 for CDMX, 15 for Estado de México)
    """
    centros = db.query(Centro).filter(Centro.estado_inegi == estado_inegi).all()
    
    # Get state name from first centro
    estado_nombre = centros[0].estado if centros else "Unknown"
    
    # Group by municipality
    by_municipio = {}
    for centro in centros:
        if centro.municipio not in by_municipio:
            by_municipio[centro.municipio] = []
        by_municipio[centro.municipio].append({
            'centro_id': centro.centro_id,
            'nombre': centro.nombre,
            'telefono': centro.telefono,
            'correo': centro.correo
        })
    
    return {
        'estado_inegi': estado_inegi,
        'estado_nombre': estado_nombre,
        'total_centros': len(centros),
        'municipios': len(by_municipio),
        'centros_by_municipio': by_municipio
    }


@router.get("/centros/stats/by-state")
async def get_centros_stats_by_state(
    db: Session = Depends(get_session)
):
    """
    Get evaluation center statistics grouped by state.
    """
    # Query to get counts by state
    stats = db.query(
        Centro.estado_inegi,
        Centro.estado,
        func.count(Centro.centro_id).label('total_centros'),
        func.count(func.distinct(Centro.municipio)).label('total_municipios')
    ).group_by(
        Centro.estado_inegi,
        Centro.estado
    ).all()
    
    # Convert to list and sort by total centers
    result = [
        {
            'estado_inegi': stat.estado_inegi,
            'estado_nombre': stat.estado,
            'total_centros': stat.total_centros,
            'total_municipios': stat.total_municipios,
            'promedio_centros_por_municipio': round(stat.total_centros / stat.total_municipios, 2) if stat.total_municipios > 0 else 0
        }
        for stat in sorted(stats, key=lambda x: x.total_centros, reverse=True)
    ]
    
    # Add national summary
    total_centros = sum(s['total_centros'] for s in result)
    total_municipios = sum(s['total_municipios'] for s in result)
    
    return {
        'national_summary': {
            'total_centros': total_centros,
            'total_estados': len(result),
            'total_municipios': total_municipios,
            'promedio_centros_por_estado': round(total_centros / len(result), 2) if result else 0
        },
        'by_state': result
    }


@router.get("/centros/nearby")
async def get_nearby_centros(
    estado_inegi: str = Query(..., description="INEGI state code"),
    municipio: Optional[str] = Query(None, description="Municipality name"),
    limit: int = Query(10, ge=1, le=50, description="Max number of results"),
    db: Session = Depends(get_session)
):
    """
    Find evaluation centers in a specific location.
    
    - **estado_inegi**: INEGI state code (required)
    - **municipio**: Municipality name (optional)
    - **limit**: Maximum number of results
    """
    query = db.query(Centro).filter(Centro.estado_inegi == estado_inegi)
    
    if municipio:
        # First try exact match
        exact_matches = query.filter(Centro.municipio == municipio).limit(limit).all()
        if exact_matches:
            return {
                'location': {
                    'estado_inegi': estado_inegi,
                    'municipio': municipio
                },
                'total_found': len(exact_matches),
                'centros': [
                    {
                        'centro_id': c.centro_id,
                        'nombre': c.nombre,
                        'municipio': c.municipio,
                        'domicilio': c.domicilio,
                        'telefono': c.telefono,
                        'correo': c.correo,
                        'coordinador': c.coordinador
                    }
                    for c in exact_matches
                ]
            }
        
        # If no exact match, try partial match
        query = query.filter(Centro.municipio.ilike(f"%{municipio}%"))
    
    centros = query.limit(limit).all()
    
    return {
        'location': {
            'estado_inegi': estado_inegi,
            'municipio': municipio or "All"
        },
        'total_found': len(centros),
        'centros': [
            {
                'centro_id': c.centro_id,
                'nombre': c.nombre,
                'municipio': c.municipio,
                'domicilio': c.domicilio,
                'telefono': c.telefono,
                'correo': c.correo,
                'coordinador': c.coordinador
            }
            for c in centros
        ]
    }