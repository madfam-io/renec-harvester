"""
Secure data access API endpoints with validation.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime

from ..auth import api_key_dependency, get_optional_api_key
from ..validators import (
    PaginationParams, 
    SearchParams, 
    DateRangeParams,
    EntityFilterParams,
    ExportRequestValidated,
    APIResponse
)
from src.models import ECStandard, Certificador, Centro, Sector
from src.models.base import get_db

router = APIRouter()


@router.get("/data/ec-standards", response_model=APIResponse)
async def get_ec_standards(
    pagination: PaginationParams = Depends(),
    filters: EntityFilterParams = Depends(),
    date_range: DateRangeParams = Depends(),
    api_key: Optional[str] = Depends(get_optional_api_key),
    db: Session = Depends(get_db)
):
    """
    Get EC Standards with filtering and pagination.
    Public endpoint with optional API key for higher rate limits.
    """
    try:
        query = db.query(ECStandard)
        
        # Apply filters
        if filters.status:
            query = query.filter(ECStandard.status == filters.status)
        if filters.sector_id:
            query = query.filter(ECStandard.sector_id == filters.sector_id)
        
        # Apply date range
        if date_range.start_date:
            query = query.filter(ECStandard.created_at >= date_range.start_date)
        if date_range.end_date:
            query = query.filter(ECStandard.created_at <= date_range.end_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.per_page
        items = query.offset(offset).limit(pagination.per_page).all()
        
        return APIResponse(
            success=True,
            message="EC Standards retrieved successfully",
            data={
                "items": [item.to_dict() for item in items],
                "total": total,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": (total + pagination.per_page - 1) // pagination.per_page
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/ec-standards/{code}", response_model=APIResponse)
async def get_ec_standard_by_code(
    code: str = Path(..., pattern="^EC\\d{4}$", description="EC Standard code"),
    api_key: Optional[str] = Depends(get_optional_api_key),
    db: Session = Depends(get_db)
):
    """
    Get a specific EC Standard by code.
    Validates EC code format (EC####).
    """
    try:
        ec_standard = db.query(ECStandard).filter(ECStandard.code == code).first()
        
        if not ec_standard:
            raise HTTPException(status_code=404, detail=f"EC Standard {code} not found")
        
        return APIResponse(
            success=True,
            message="EC Standard retrieved successfully",
            data=ec_standard.to_dict()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/search", response_model=APIResponse)
async def search_entities(
    search: SearchParams,
    entity_type: str = Query(..., pattern="^(ec_standard|certificador|centro|sector|all)$"),
    api_key: str = Depends(api_key_dependency),
    db: Session = Depends(get_db)
):
    """
    Search across entity types with validated query.
    Requires API key.
    """
    try:
        results = []
        
        # Map entity types to models
        entity_models = {
            "ec_standard": ECStandard,
            "certificador": Certificador,
            "centro": Centro,
            "sector": Sector
        }
        
        # Search in specified entity type or all
        models_to_search = [entity_models[entity_type]] if entity_type != "all" else entity_models.values()
        
        for model in models_to_search:
            query = db.query(model)
            
            # Simple text search (can be enhanced with full-text search)
            if hasattr(model, 'name'):
                query = query.filter(model.name.ilike(f"%{search.q}%"))
            elif hasattr(model, 'title'):
                query = query.filter(model.title.ilike(f"%{search.q}%"))
            
            items = query.limit(10).all()
            for item in items:
                result = item.to_dict()
                result['_type'] = model.__tablename__
                results.append(result)
        
        return APIResponse(
            success=True,
            message=f"Found {len(results)} results",
            data=results
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/export", response_model=APIResponse)
async def export_data(
    export_request: ExportRequestValidated,
    api_key: str = Depends(api_key_dependency),
    db: Session = Depends(get_db)
):
    """
    Export data with validated format and filters.
    Requires API key.
    """
    try:
        # Validate export format and entity type
        if export_request.entity_type == "all" and export_request.format != "json":
            raise HTTPException(
                status_code=400, 
                detail="Export format 'all' only supports JSON format"
            )
        
        # TODO: Implement actual export logic
        # This is a placeholder response
        export_id = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return APIResponse(
            success=True,
            message="Export request accepted",
            data={
                "export_id": export_id,
                "status": "processing",
                "format": export_request.format,
                "estimated_time": "2-5 minutes"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/stats", response_model=APIResponse)
async def get_statistics(
    api_key: Optional[str] = Depends(get_optional_api_key),
    db: Session = Depends(get_db)
):
    """
    Get database statistics.
    Public endpoint with caching.
    """
    try:
        stats = {
            "ec_standards": db.query(ECStandard).count(),
            "certificadores": db.query(Certificador).count(),
            "centros": db.query(Centro).count(),
            "sectores": db.query(Sector).count(),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))