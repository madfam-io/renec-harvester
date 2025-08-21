"""
Sectores and Comités API endpoints.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models import get_session
from src.models.sector import Sector
from src.models.comite import Comite
from src.api.models import SectorResponse, SectorDetail, ComiteResponse, ComiteDetail


router = APIRouter()


@router.get("/sectores", response_model=List[SectorResponse])
async def list_sectores(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    search: Optional[str] = Query(None, description="Search in sector name"),
    db: Session = Depends(get_session)
):
    """
    List productive sectors with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **search**: Search in sector name
    """
    query = select(Sector)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(Sector.nombre.ilike(search_term))
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Sector.sector_id)
    
    # Execute query
    result = db.execute(query)
    sectores = result.scalars().all()
    
    # Get EC standard counts for each sector
    from src.models import ECStandardV2 as ECStandard
    sector_counts = {}
    for sector in sectores:
        count = db.query(func.count(ECStandard.ec_clave)).filter(
            ECStandard.sector_id == sector.sector_id
        ).scalar()
        sector_counts[sector.sector_id] = count
    
    return [
        SectorResponse(
            sector_id=sector.sector_id,
            nombre=sector.nombre,
            descripcion=sector.descripcion,
            total_ec_standards=sector_counts.get(sector.sector_id, 0),
            last_seen=sector.last_seen
        )
        for sector in sectores
    ]


@router.get("/sectores/{sector_id}", response_model=SectorDetail)
async def get_sector(
    sector_id: int,
    db: Session = Depends(get_session)
):
    """
    Get detailed information for a specific sector.
    
    - **sector_id**: The sector ID
    """
    sector = db.query(Sector).filter(Sector.sector_id == sector_id).first()
    
    if not sector:
        raise HTTPException(status_code=404, detail=f"Sector {sector_id} not found")
    
    # Get committees in this sector
    comites = db.query(Comite).filter(Comite.sector_id == sector_id).all()
    
    # Get EC standards count
    from src.models import ECStandardV2 as ECStandard
    ec_count = db.query(func.count(ECStandard.ec_clave)).filter(
        ECStandard.sector_id == sector_id
    ).scalar()
    
    # Get sample EC standards
    sample_standards = db.query(ECStandard).filter(
        ECStandard.sector_id == sector_id
    ).limit(10).all()
    
    return SectorDetail(
        sector_id=sector.sector_id,
        nombre=sector.nombre,
        descripcion=sector.descripcion,
        src_url=sector.src_url,
        first_seen=sector.first_seen,
        last_seen=sector.last_seen,
        total_ec_standards=ec_count,
        total_comites=len(comites),
        comites=[
            {
                'comite_id': c.comite_id,
                'nombre': c.nombre
            }
            for c in comites
        ],
        sample_ec_standards=[
            {
                'ec_clave': ec.ec_clave,
                'titulo': ec.titulo,
                'vigente': ec.vigente
            }
            for ec in sample_standards
        ]
    )


@router.get("/sectores/{sector_id}/ec-standards")
async def get_sector_standards(
    sector_id: int,
    vigente: Optional[bool] = Query(None, description="Filter by vigente status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_session)
):
    """
    Get all EC standards in a specific sector.
    """
    # Verify sector exists
    sector = db.query(Sector).filter(Sector.sector_id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail=f"Sector {sector_id} not found")
    
    from src.models import ECStandardV2 as ECStandard
    
    query = db.query(ECStandard).filter(ECStandard.sector_id == sector_id)
    
    if vigente is not None:
        query = query.filter(ECStandard.vigente == vigente)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    standards = query.offset(skip).limit(limit).all()
    
    return {
        'sector_id': sector_id,
        'nombre': sector.nombre,
        'total_standards': total,
        'showing': len(standards),
        'ec_standards': [
            {
                'ec_clave': ec.ec_clave,
                'titulo': ec.titulo,
                'version': ec.version,
                'vigente': ec.vigente,
                'comite': ec.comite,
                'nivel': ec.nivel,
                'duracion_horas': ec.duracion_horas
            }
            for ec in standards
        ]
    }


@router.get("/comites", response_model=List[ComiteResponse])
async def list_comites(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    sector_id: Optional[int] = Query(None, description="Filter by sector ID"),
    search: Optional[str] = Query(None, description="Search in committee name"),
    db: Session = Depends(get_session)
):
    """
    List management committees with pagination and filtering.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **sector_id**: Filter by sector ID
    - **search**: Search in committee name
    """
    query = select(Comite)
    
    # Apply filters
    if sector_id is not None:
        query = query.where(Comite.sector_id == sector_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(Comite.nombre.ilike(search_term))
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Comite.comite_id)
    
    # Execute query
    result = db.execute(query)
    comites = result.scalars().all()
    
    # Get EC standard counts for each committee
    from src.models import ECStandardV2 as ECStandard
    comite_counts = {}
    for comite in comites:
        count = db.query(func.count(ECStandard.ec_clave)).filter(
            ECStandard.comite_id == comite.comite_id
        ).scalar()
        comite_counts[comite.comite_id] = count
    
    # Get sector names
    sector_names = {}
    for comite in comites:
        if comite.sector_id and comite.sector_id not in sector_names:
            sector = db.query(Sector).filter(Sector.sector_id == comite.sector_id).first()
            if sector:
                sector_names[comite.sector_id] = sector.nombre
    
    return [
        ComiteResponse(
            comite_id=comite.comite_id,
            nombre=comite.nombre,
            sector_id=comite.sector_id,
            sector_nombre=sector_names.get(comite.sector_id, "Unknown"),
            total_ec_standards=comite_counts.get(comite.comite_id, 0),
            last_seen=comite.last_seen
        )
        for comite in comites
    ]


@router.get("/comites/{comite_id}", response_model=ComiteDetail)
async def get_comite(
    comite_id: int,
    db: Session = Depends(get_session)
):
    """
    Get detailed information for a specific committee.
    
    - **comite_id**: The committee ID
    """
    comite = db.query(Comite).filter(Comite.comite_id == comite_id).first()
    
    if not comite:
        raise HTTPException(status_code=404, detail=f"Comité {comite_id} not found")
    
    # Get sector info
    sector_info = None
    if comite.sector_id:
        sector = db.query(Sector).filter(Sector.sector_id == comite.sector_id).first()
        if sector:
            sector_info = {
                'sector_id': sector.sector_id,
                'nombre': sector.nombre
            }
    
    # Get EC standards count
    from src.models import ECStandardV2 as ECStandard
    ec_count = db.query(func.count(ECStandard.ec_clave)).filter(
        ECStandard.comite_id == comite_id
    ).scalar()
    
    # Get sample EC standards
    sample_standards = db.query(ECStandard).filter(
        ECStandard.comite_id == comite_id
    ).limit(10).all()
    
    return ComiteDetail(
        comite_id=comite.comite_id,
        nombre=comite.nombre,
        sector_id=comite.sector_id,
        descripcion=comite.descripcion,
        institucion_representada=comite.institucion_representada,
        src_url=comite.src_url,
        first_seen=comite.first_seen,
        last_seen=comite.last_seen,
        sector=sector_info,
        total_ec_standards=ec_count,
        sample_ec_standards=[
            {
                'ec_clave': ec.ec_clave,
                'titulo': ec.titulo,
                'vigente': ec.vigente
            }
            for ec in sample_standards
        ]
    )


@router.get("/comites/{comite_id}/ec-standards")
async def get_comite_standards(
    comite_id: int,
    vigente: Optional[bool] = Query(None, description="Filter by vigente status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_session)
):
    """
    Get all EC standards managed by a specific committee.
    """
    # Verify comite exists
    comite = db.query(Comite).filter(Comite.comite_id == comite_id).first()
    if not comite:
        raise HTTPException(status_code=404, detail=f"Comité {comite_id} not found")
    
    from src.models import ECStandardV2 as ECStandard
    
    query = db.query(ECStandard).filter(ECStandard.comite_id == comite_id)
    
    if vigente is not None:
        query = query.filter(ECStandard.vigente == vigente)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    standards = query.offset(skip).limit(limit).all()
    
    return {
        'comite_id': comite_id,
        'nombre': comite.nombre,
        'sector_id': comite.sector_id,
        'total_standards': total,
        'showing': len(standards),
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


@router.get("/sectores/stats/summary")
async def get_sectores_stats(
    db: Session = Depends(get_session)
):
    """
    Get overall statistics for sectors and committees.
    """
    from src.models import ECStandardV2 as ECStandard
    from src.models.relations import ECSector
    
    # Get sector statistics
    sector_stats = db.query(
        Sector.sector_id,
        Sector.nombre,
        func.count(func.distinct(ECStandard.ec_clave)).label('total_standards'),
        func.count(func.distinct(Comite.comite_id)).label('total_comites')
    ).outerjoin(
        ECStandard, ECStandard.sector_id == Sector.sector_id
    ).outerjoin(
        Comite, Comite.sector_id == Sector.sector_id
    ).group_by(
        Sector.sector_id,
        Sector.nombre
    ).all()
    
    # Convert to list
    sectors_data = [
        {
            'sector_id': stat.sector_id,
            'nombre': stat.nombre,
            'total_standards': stat.total_standards,
            'total_comites': stat.total_comites
        }
        for stat in sorted(sector_stats, key=lambda x: x.total_standards, reverse=True)
    ]
    
    # Get overall counts
    total_sectors = db.query(func.count(Sector.sector_id)).scalar()
    total_comites = db.query(func.count(Comite.comite_id)).scalar()
    total_standards = db.query(func.count(func.distinct(ECStandard.ec_clave))).scalar()
    vigente_standards = db.query(func.count(ECStandard.ec_clave)).filter(
        ECStandard.vigente == True
    ).scalar()
    
    return {
        'summary': {
            'total_sectors': total_sectors,
            'total_comites': total_comites,
            'total_ec_standards': total_standards,
            'vigente_ec_standards': vigente_standards,
            'inactive_ec_standards': total_standards - vigente_standards
        },
        'top_sectors': sectors_data[:10],  # Top 10 sectors by EC count
        'sectors_without_standards': [
            s for s in sectors_data if s['total_standards'] == 0
        ]
    }