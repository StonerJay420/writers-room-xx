"""Reports router for managing and serving report artifacts via CDN."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..storage.s3 import storage


router = APIRouter(prefix="/reports", tags=["reports"])


class ReportItem(BaseModel):
    """Report item response model."""
    key: str
    cdn_url: str
    size: int
    last_modified: str


class ReportUploadResponse(BaseModel):
    """Report upload response model."""
    success: bool
    key: str
    cdn_url: str


@router.get("/list", response_model=List[ReportItem])
async def list_reports(prefix: Optional[str] = None):
    """List all reports with CDN URLs."""
    try:
        objects = storage.list_objects(prefix=prefix or "reports/")
        
        return [
            ReportItem(
                key=obj['key'],
                cdn_url=obj['cdn_url'],
                size=obj['size'],
                last_modified=obj['last_modified']
            )
            for obj in objects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=ReportUploadResponse)
async def upload_report(
    file: UploadFile = File(...),
    cache_hours: int = Form(default=24)
):
    """Upload a report with cache control."""
    try:
        # Generate key with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        key = f"reports/{timestamp}_{file.filename}"
        
        # Calculate cache control
        cache_control = f"public, max-age={cache_hours * 3600}"
        
        # Upload to S3/Spaces
        content = await file.read()
        success = storage.put_object_with_cache(
            key=key,
            body=content,
            content_type=file.content_type or "application/octet-stream",
            cache_control=cache_control
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Upload failed")
        
        cdn_url = storage.generate_cdn_url(key)
        
        return ReportUploadResponse(
            success=True,
            key=key,
            cdn_url=cdn_url
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))