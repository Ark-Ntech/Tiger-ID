"""API routes for exporting investigations"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, JSONResponse
from typing import Optional, Any
from uuid import UUID

from backend.auth.auth import get_current_user
from backend.database import get_db, User
from backend.services.export_service import get_export_service
from backend.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/investigations", tags=["export"])


def serialize_enums(obj: Any) -> Any:
    """Recursively convert enum objects to their values for JSON serialization"""
    if hasattr(obj, 'value'):
        return obj.value
    elif isinstance(obj, dict):
        return {k: serialize_enums(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_enums(item) for item in obj]
    else:
        return obj


@router.get("/{investigation_id}/export/json")
async def export_investigation_json(
    investigation_id: UUID,
    include_evidence: bool = Query(True, description="Include evidence items"),
    include_steps: bool = Query(True, description="Include investigation steps"),
    include_metadata: bool = Query(True, description="Include metadata"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Export investigation as JSON"""
    service = get_export_service(db)
    export_data = service.export_investigation_json(
        investigation_id,
        include_evidence=include_evidence,
        include_steps=include_steps,
        include_metadata=include_metadata
    )
    
    if "error" in export_data:
        raise HTTPException(status_code=404, detail=export_data["error"])
    
    # Convert any enum objects to their values for JSON serialization
    serializable_data = serialize_enums(export_data)
    
    return JSONResponse(
        content=serializable_data,
        headers={
            "Content-Disposition": f"attachment; filename=investigation_{investigation_id}.json"
        }
    )


@router.get("/{investigation_id}/export/markdown")
async def export_investigation_markdown(
    investigation_id: UUID,
    include_evidence: bool = Query(True, description="Include evidence items"),
    include_steps: bool = Query(True, description="Include investigation steps"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Export investigation as Markdown"""
    service = get_export_service(db)
    markdown_content = service.export_investigation_markdown(
        investigation_id,
        include_evidence=include_evidence,
        include_steps=include_steps
    )
    
    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=investigation_{investigation_id}.md"
        }
    )


@router.get("/{investigation_id}/export/pdf")
async def export_investigation_pdf(
    investigation_id: UUID,
    include_evidence: bool = Query(True, description="Include evidence items"),
    include_steps: bool = Query(True, description="Include investigation steps"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Export investigation as PDF"""
    service = get_export_service(db)
    
    try:
        pdf_bytes = service.export_investigation_pdf(
            investigation_id,
            include_evidence=include_evidence,
            include_steps=include_steps
        )
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=investigation_{investigation_id}.pdf"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/{investigation_id}/export/csv")
async def export_investigation_csv(
    investigation_id: UUID,
    data_type: str = Query("evidence", description="Type of data to export (evidence, steps, summary)"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Export investigation data as CSV"""
    service = get_export_service(db)
    
    if data_type not in ["evidence", "steps", "summary"]:
        raise HTTPException(status_code=400, detail="Invalid data_type. Must be 'evidence', 'steps', or 'summary'")
    
    csv_content = service.export_investigation_csv(investigation_id, data_type=data_type)
    
    if csv_content.startswith("Error:"):
        raise HTTPException(status_code=404, detail=csv_content)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=investigation_{investigation_id}_{data_type}.csv"
        }
    )

