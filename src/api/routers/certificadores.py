"""
Certificadores API endpoints.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models import get_session, CertificadorV2 as Certificador
from src.api.models import PaginationParams, CertificadorResponse, CertificadorDetail


router = APIRouter()


@router.get("/certificadores", response_model=List[CertificadorResponse])
async def list_certificadores(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    tipo: Optional[str] = Query(None, description="Filter by type (ECE/OC)"),
    estado_inegi: Optional[str] = Query(None, description="Filter by INEGI state code"),
    estatus: Optional[str] = Query(None, description="Filter by status (Vigente/Cancelado)"),
    search: Optional[str] = Query(None, description="Search in ID, name, and acronym"),
    db: Session = Depends(get_session)
):
    """
    List certificadores with pagination and filtering.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **tipo**: Filter by certificador type (ECE or OC)
    - **estado_inegi**: Filter by INEGI state code (e.g., 09 for CDMX)
    - **estatus**: Filter by status (Vigente or Cancelado)
    - **search**: Search in ID, legal name, and acronym
    """
    query = select(Certificador)
    
    # Apply filters
    if tipo:
        query = query.where(Certificador.tipo == tipo.upper())
    
    if estado_inegi:
        query = query.where(Certificador.estado_inegi == estado_inegi)
    
    if estatus:
        query = query.where(Certificador.estatus == estatus)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Certificador.cert_id.ilike(search_term)) |
            (Certificador.nombre_legal.ilike(search_term)) |
            (Certificador.siglas.ilike(search_term))
        )
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = db.execute(query)
    certificadores = result.scalars().all()
    
    return [
        CertificadorResponse(
            cert_id=cert.cert_id,
            tipo=cert.tipo,
            nombre_legal=cert.nombre_legal,
            siglas=cert.siglas,
            estatus=cert.estatus,
            estado=cert.estado,
            estado_inegi=cert.estado_inegi,
            municipio=cert.municipio,
            telefono=cert.telefono,
            correo=cert.correo,
            last_seen=cert.last_seen
        )
        for cert in certificadores
    ]


@router.get("/certificadores/{cert_id}", response_model=CertificadorDetail)
async def get_certificador(
    cert_id: str,
    db: Session = Depends(get_session)
):
    """
    Get detailed information for a specific certificador.
    
    - **cert_id**: The certificador ID (e.g., ECE001-99)
    """
    cert = db.query(Certificador).filter(Certificador.cert_id == cert_id).first()
    
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificador {cert_id} not found")
    
    # Get accredited EC standards
    from src.models.relations import ECEEC
    from src.models import ECStandardV2 as ECStandard
    
    ec_standards = []
    if cert.tipo == 'ECE':
        ece_relations = db.query(ECEEC).filter(ECEEC.cert_id == cert_id).all()
        
        for rel in ece_relations:
            ec = db.query(ECStandard).filter(ECStandard.ec_clave == rel.ec_clave).first()
            if ec:
                ec_standards.append({
                    'ec_clave': ec.ec_clave,
                    'titulo': ec.titulo,
                    'vigente': ec.vigente,
                    'sector': ec.sector,
                    'acreditado_desde': rel.acreditado_desde
                })
    
    return CertificadorDetail(
        cert_id=cert.cert_id,
        tipo=cert.tipo,
        nombre_legal=cert.nombre_legal,
        siglas=cert.siglas,
        estatus=cert.estatus,
        domicilio_texto=cert.domicilio_texto,
        estado=cert.estado,
        estado_inegi=cert.estado_inegi,
        municipio=cert.municipio,
        cp=cert.cp,
        telefono=cert.telefono,
        correo=cert.correo,
        sitio_web=cert.sitio_web,
        representante_legal=cert.representante_legal,
        fecha_acreditacion=cert.fecha_acreditacion,
        contactos_adicionales=cert.contactos_adicionales,
        src_url=cert.src_url,
        first_seen=cert.first_seen,
        last_seen=cert.last_seen,
        ec_standards=ec_standards
    )


@router.get("/certificadores/{cert_id}/ec-standards")
async def get_certificador_standards(
    cert_id: str,
    vigente: Optional[bool] = Query(None, description="Filter by vigente status"),
    db: Session = Depends(get_session)
):
    """
    Get all EC standards that this certificador can accredit.
    """
    # Verify certificador exists
    cert = db.query(Certificador).filter(Certificador.cert_id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificador {cert_id} not found")
    
    # Only ECE type can accredit standards
    if cert.tipo != 'ECE':
        return {
            'cert_id': cert_id,
            'nombre_legal': cert.nombre_legal,
            'tipo': cert.tipo,
            'total_standards': 0,
            'ec_standards': [],
            'message': 'Only ECE (Entidad de Certificación y Evaluación) can accredit standards'
        }
    
    from src.models.relations import ECEEC
    from src.models import ECStandardV2 as ECStandard
    
    query = db.query(ECStandard).join(
        ECEEC, ECEEC.ec_clave == ECStandard.ec_clave
    ).filter(ECEEC.cert_id == cert_id)
    
    if vigente is not None:
        query = query.filter(ECStandard.vigente == vigente)
    
    standards = query.all()
    
    # Get accreditation dates
    ece_relations = {rel.ec_clave: rel for rel in 
                     db.query(ECEEC).filter(ECEEC.cert_id == cert_id).all()}
    
    return {
        'cert_id': cert_id,
        'nombre_legal': cert.nombre_legal,
        'tipo': cert.tipo,
        'total_standards': len(standards),
        'ec_standards': [
            {
                'ec_clave': ec.ec_clave,
                'titulo': ec.titulo,
                'version': ec.version,
                'vigente': ec.vigente,
                'sector': ec.sector,
                'nivel': ec.nivel,
                'acreditado_desde': ece_relations.get(ec.ec_clave).acreditado_desde
            }
            for ec in standards
        ]
    }


@router.get("/certificadores/by-state/{estado_inegi}")
async def get_certificadores_by_state(
    estado_inegi: str,
    tipo: Optional[str] = Query(None, description="Filter by type (ECE/OC)"),
    db: Session = Depends(get_session)
):
    """
    Get all certificadores in a specific state.
    
    - **estado_inegi**: INEGI state code (e.g., 09 for CDMX, 15 for Estado de México)
    """
    query = db.query(Certificador).filter(Certificador.estado_inegi == estado_inegi)
    
    if tipo:
        query = query.filter(Certificador.tipo == tipo.upper())
    
    certificadores = query.all()
    
    # Get state name from first certificador
    estado_nombre = certificadores[0].estado if certificadores else "Unknown"
    
    return {
        'estado_inegi': estado_inegi,
        'estado_nombre': estado_nombre,
        'total': len(certificadores),
        'by_tipo': {
            'ECE': len([c for c in certificadores if c.tipo == 'ECE']),
            'OC': len([c for c in certificadores if c.tipo == 'OC'])
        },
        'certificadores': [
            {
                'cert_id': cert.cert_id,
                'tipo': cert.tipo,
                'nombre_legal': cert.nombre_legal,
                'siglas': cert.siglas,
                'estatus': cert.estatus,
                'municipio': cert.municipio,
                'telefono': cert.telefono,
                'correo': cert.correo
            }
            for cert in certificadores
        ]
    }


@router.get("/certificadores/stats/by-state")
async def get_certificadores_stats_by_state(
    db: Session = Depends(get_session)
):
    """
    Get certificador statistics grouped by state.
    """
    # Query to get counts by state and type
    stats = db.query(
        Certificador.estado_inegi,
        Certificador.estado,
        Certificador.tipo,
        func.count(Certificador.cert_id).label('count')
    ).group_by(
        Certificador.estado_inegi,
        Certificador.estado,
        Certificador.tipo
    ).all()
    
    # Organize by state
    state_stats = {}
    for stat in stats:
        if stat.estado_inegi not in state_stats:
            state_stats[stat.estado_inegi] = {
                'estado_inegi': stat.estado_inegi,
                'estado_nombre': stat.estado,
                'total': 0,
                'ECE': 0,
                'OC': 0
            }
        
        state_stats[stat.estado_inegi][stat.tipo] = stat.count
        state_stats[stat.estado_inegi]['total'] += stat.count
    
    # Convert to list and sort by total
    result = sorted(
        state_stats.values(),
        key=lambda x: x['total'],
        reverse=True
    )
    
    # Add national summary
    total_ece = sum(s['ECE'] for s in result)
    total_oc = sum(s['OC'] for s in result)
    
    return {
        'national_summary': {
            'total_certificadores': total_ece + total_oc,
            'total_ECE': total_ece,
            'total_OC': total_oc
        },
        'by_state': result
    }