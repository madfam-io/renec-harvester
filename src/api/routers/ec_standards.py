"""
EC Standards API endpoints.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models import get_session, ECStandardV2 as ECStandard
from src.api.models import PaginationParams, ECStandardResponse, ECStandardDetail


router = APIRouter()


@router.get("/ec-standards", response_model=List[ECStandardResponse])
async def list_ec_standards(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    vigente: Optional[bool] = Query(None, description="Filter by vigente status"),
    sector_id: Optional[int] = Query(None, description="Filter by sector ID"),
    search: Optional[str] = Query(None, description="Search in code and title"),
    db: Session = Depends(get_session)
):
    """
    List EC standards with pagination and filtering.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **vigente**: Filter by active/inactive status
    - **sector_id**: Filter by sector ID
    - **search**: Search in EC code and title
    """
    query = select(ECStandard)
    
    # Apply filters
    if vigente is not None:
        query = query.where(ECStandard.vigente == vigente)
    
    if sector_id is not None:
        query = query.where(ECStandard.sector_id == sector_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (ECStandard.ec_clave.ilike(search_term)) |
            (ECStandard.titulo.ilike(search_term))
        )
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = db.execute(query)
    standards = result.scalars().all()
    
    return [
        ECStandardResponse(
            ec_clave=ec.ec_clave,
            titulo=ec.titulo,
            version=ec.version,
            vigente=ec.vigente,
            sector=ec.sector,
            sector_id=ec.sector_id,
            nivel=ec.nivel,
            duracion_horas=ec.duracion_horas,
            last_seen=ec.last_seen
        )
        for ec in standards
    ]


@router.get("/ec-standards/{ec_clave}", response_model=ECStandardDetail)
async def get_ec_standard(
    ec_clave: str,
    db: Session = Depends(get_session)
):
    """
    Get detailed information for a specific EC standard.
    
    - **ec_clave**: The EC standard code (e.g., EC0217)
    """
    ec = db.query(ECStandard).filter(ECStandard.ec_clave == ec_clave).first()
    
    if not ec:
        raise HTTPException(status_code=404, detail=f"EC standard {ec_clave} not found")
    
    # Get related certificadores
    from src.models.relations import ECEEC
    from src.models import CertificadorV2 as Certificador
    
    certificadores = []
    ece_relations = db.query(ECEEC).filter(ECEEC.ec_clave == ec_clave).all()
    
    for rel in ece_relations:
        cert = db.query(Certificador).filter(Certificador.cert_id == rel.cert_id).first()
        if cert:
            certificadores.append({
                'cert_id': cert.cert_id,
                'tipo': cert.tipo,
                'nombre_legal': cert.nombre_legal,
                'estado': cert.estado
            })
    
    return ECStandardDetail(
        ec_clave=ec.ec_clave,
        titulo=ec.titulo,
        version=ec.version,
        vigente=ec.vigente,
        sector=ec.sector,
        sector_id=ec.sector_id,
        comite=ec.comite,
        comite_id=ec.comite_id,
        descripcion=ec.descripcion,
        competencias=ec.competencias,
        nivel=ec.nivel,
        duracion_horas=ec.duracion_horas,
        tipo_norma=ec.tipo_norma,
        fecha_publicacion=ec.fecha_publicacion,
        fecha_vigencia=ec.fecha_vigencia,
        perfil_evaluador=ec.perfil_evaluador,
        criterios_evaluacion=ec.criterios_evaluacion,
        renec_url=ec.renec_url,
        first_seen=ec.first_seen,
        last_seen=ec.last_seen,
        certificadores=certificadores
    )


@router.get("/ec-standards/{ec_clave}/certificadores")
async def get_ec_certificadores(
    ec_clave: str,
    db: Session = Depends(get_session)
):
    """
    Get all certificadores that can accredit this EC standard.
    """
    # Verify EC exists
    ec = db.query(ECStandard).filter(ECStandard.ec_clave == ec_clave).first()
    if not ec:
        raise HTTPException(status_code=404, detail=f"EC standard {ec_clave} not found")
    
    from src.models.relations import ECEEC
    from src.models import CertificadorV2 as Certificador
    
    certificadores = []
    ece_relations = db.query(ECEEC).filter(ECEEC.ec_clave == ec_clave).all()
    
    for rel in ece_relations:
        cert = db.query(Certificador).filter(Certificador.cert_id == rel.cert_id).first()
        if cert:
            certificadores.append({
                'cert_id': cert.cert_id,
                'tipo': cert.tipo,
                'nombre_legal': cert.nombre_legal,
                'siglas': cert.siglas,
                'estado': cert.estado,
                'estado_inegi': cert.estado_inegi,
                'estatus': cert.estatus,
                'correo': cert.correo,
                'telefono': cert.telefono,
                'acreditado_desde': rel.acreditado_desde
            })
    
    return {
        'ec_clave': ec_clave,
        'titulo': ec.titulo,
        'total_certificadores': len(certificadores),
        'certificadores': certificadores
    }


@router.get("/ec-standards/{ec_clave}/centros")
async def get_ec_centros(
    ec_clave: str,
    estado_inegi: Optional[str] = Query(None, description="Filter by INEGI state code"),
    db: Session = Depends(get_session)
):
    """
    Get all evaluation centers that can evaluate this EC standard.
    """
    # Verify EC exists
    ec = db.query(ECStandard).filter(ECStandard.ec_clave == ec_clave).first()
    if not ec:
        raise HTTPException(status_code=404, detail=f"EC standard {ec_clave} not found")
    
    from src.models.relations import CentroEC
    from src.models.centro import Centro
    
    query = db.query(Centro).join(
        CentroEC, CentroEC.centro_id == Centro.centro_id
    ).filter(CentroEC.ec_clave == ec_clave)
    
    if estado_inegi:
        query = query.filter(Centro.estado_inegi == estado_inegi)
    
    centros = query.all()
    
    return {
        'ec_clave': ec_clave,
        'titulo': ec.titulo,
        'total_centros': len(centros),
        'centros': [
            {
                'centro_id': centro.centro_id,
                'nombre': centro.nombre,
                'estado': centro.estado,
                'estado_inegi': centro.estado_inegi,
                'municipio': centro.municipio,
                'telefono': centro.telefono,
                'correo': centro.correo
            }
            for centro in centros
        ]
    }