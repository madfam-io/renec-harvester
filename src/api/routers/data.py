"""
Data access and export API endpoints.
"""
from fastapi import APIRouter, Query, HTTPException, Response
from typing import Optional, List
from datetime import datetime
import json
import csv
import io

from ..models import DataResponse, DataItem, ExportFormat

router = APIRouter()


@router.get("/data", response_model=DataResponse)
async def get_data(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    type_filter: Optional[str] = Query(None, alias="type"),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None)
):
    """Get paginated data with optional filtering and search."""
    try:
        # Mock data for development - replace with actual database queries
        mock_items = [
            DataItem(
                id="1",
                type="ec_standard",
                title="Instalación de sistemas de aire acondicionado",
                code="EC0221",
                sector="Construcción",
                last_updated=datetime.now(),
                status="active"
            ),
            DataItem(
                id="2", 
                type="certificador",
                title="Instituto Nacional de Certificación",
                code="CERT001", 
                sector="Educación",
                last_updated=datetime.now(),
                status="active"
            ),
            DataItem(
                id="3",
                type="course",
                title="Curso de Soldadura Industrial",
                code="CURSO-SOL-001",
                sector="Manufactura", 
                last_updated=datetime.now(),
                status="pending"
            ),
            DataItem(
                id="4",
                type="evaluation_center",
                title="Centro de Evaluación Técnica Industrial",
                code="CETI-001",
                sector="Industria",
                last_updated=datetime.now(),
                status="active"
            ),
            DataItem(
                id="5",
                type="sector",
                title="Sector de Tecnologías de la Información",
                code="SECT-TI",
                sector="Tecnología",
                last_updated=datetime.now(), 
                status="active"
            )
        ]
        
        # Apply filters
        filtered_items = mock_items
        
        if type_filter:
            filtered_items = [item for item in filtered_items if item.type == type_filter]
        
        if status_filter:
            filtered_items = [item for item in filtered_items if item.status == status_filter]
        
        if search:
            search_lower = search.lower()
            filtered_items = [
                item for item in filtered_items
                if search_lower in item.title.lower() or search_lower in item.code.lower()
            ]
        
        # Apply pagination
        total = len(filtered_items)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_items = filtered_items[start_idx:end_idx]
        
        return DataResponse(
            items=paginated_items,
            total=total,
            page=page,
            per_page=per_page
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/{item_id}")
async def get_data_item(item_id: str):
    """Get detailed information for a specific data item."""
    try:
        # Mock detailed data - replace with actual database query
        if item_id == "1":
            return {
                "id": "1",
                "type": "ec_standard",
                "title": "Instalación de sistemas de aire acondicionado",
                "code": "EC0221", 
                "sector": "Construcción",
                "last_updated": datetime.now().isoformat(),
                "status": "active",
                "data": {
                    "description": "Estándar para la instalación y mantenimiento de sistemas de aire acondicionado",
                    "competencies": [
                        "Diagnóstico de sistemas",
                        "Instalación de equipos",
                        "Mantenimiento preventivo"
                    ],
                    "duration_hours": 120,
                    "certification_body": "CONOCER",
                    "validity_years": 3
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_data(
    format: ExportFormat = Query(ExportFormat.JSON),
    type_filter: Optional[str] = Query(None, alias="type"),
    status_filter: Optional[str] = Query(None, alias="status")
):
    """Export data in various formats (JSON, CSV, Excel)."""
    try:
        # Get data using same filtering logic as /data endpoint
        data_response = await get_data(
            page=1,
            per_page=10000,  # Large number to get all data
            type_filter=type_filter,
            status_filter=status_filter
        )
        
        items = data_response.items
        
        if format == ExportFormat.JSON:
            # Export as JSON
            export_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "total_items": len(items),
                    "filters": {
                        "type": type_filter,
                        "status": status_filter
                    }
                },
                "data": [item.dict() for item in items]
            }
            
            return Response(
                content=json.dumps(export_data, default=str, indent=2),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=renec_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
            )
        
        elif format == ExportFormat.CSV:
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["ID", "Type", "Title", "Code", "Sector", "Status", "Last Updated"])
            
            # Write data rows
            for item in items:
                writer.writerow([
                    item.id,
                    item.type,
                    item.title,
                    item.code,
                    item.sector or "",
                    item.status,
                    item.last_updated.isoformat()
                ])
            
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=renec_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Export format {format} not implemented yet")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_data_summary():
    """Get summary statistics of available data."""
    try:
        # Mock summary data - replace with actual database aggregations
        summary = {
            "total_items": 4765,
            "by_type": {
                "ec_standard": 1250,
                "certificador": 890,
                "evaluation_center": 450,
                "course": 2100,
                "sector": 75
            },
            "by_status": {
                "active": 4234,
                "pending": 456,
                "error": 75
            },
            "by_sector": {
                "Construcción": 1200,
                "Educación": 890,
                "Manufactura": 1100,
                "Tecnología": 675,
                "Servicios": 900
            },
            "last_updated": datetime.now().isoformat(),
            "data_freshness": {
                "last_24h": 234,
                "last_week": 1456,
                "last_month": 3890
            }
        }
        
        return summary
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))