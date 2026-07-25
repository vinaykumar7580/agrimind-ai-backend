from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User, Scan
from auth import get_current_user
from agents.crop_agent import analyze_crop_image
from agents.soil_agent import analyze_soil_image
from services.image_service import save_image
from services.gemini_service import GeminiUnavailableError

router = APIRouter(prefix="/scan", tags=["scan"])

@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    scan_type: str = Form(...),  # "crop" or "soil"
    location: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if scan_type not in ("crop", "soil"):
        raise HTTPException(status_code=400, detail="scan_type must be 'crop' or 'soil'")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    # Save image
    image_path = save_image(image_bytes, prefix=scan_type)

    # User context for better AI response
    user_ctx = {
        "state": current_user.state,
        "district": current_user.district,
        "farming_type": current_user.farming_type,
        "primary_crops": current_user.primary_crops,
    }

    # Run appropriate agent
    try:
        if scan_type == "crop":
            result = await analyze_crop_image(image_bytes, user_ctx)
        else:
            result = await analyze_soil_image(image_bytes, user_ctx)
    except GeminiUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if scan_type == "crop":
        scan = Scan(
            user_id=current_user.id,
            scan_type="crop",
            image_path=image_path,
            crop_name=result.get("crop_name"),
            crop_variety=result.get("growth_stage"),
            health_score=result.get("health_score"),
            disease=result.get("disease"),
            severity=result.get("severity", "none"),
            findings=result.get("findings", []),
            treatment=result.get("treatment", []),
            ai_summary=result.get("ai_summary"),
            status="pending" if result.get("severity") not in ("none",) else "healthy",
            location=location or current_user.district,
        )
    else:
        scan = Scan(
            user_id=current_user.id,
            scan_type="soil",
            image_path=image_path,
            health_score=result.get("overall_health"),
            soil_data=result,
            ai_summary=result.get("ai_summary"),
            status="pending",
            location=location or current_user.district,
        )

    db.add(scan)
    db.commit()
    db.refresh(scan)

    return {"scan_id": scan.id, "result": result, "image_url": f"/uploads/{image_path.split('/')[-1]}"}

@router.get("/history")
def scan_history(
    skip: int = 0,
    limit: int = 20,
    scan_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Scan).filter(Scan.user_id == current_user.id)
    if scan_type:
        q = q.filter(Scan.scan_type == scan_type)
    scans = q.order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()
    return [_scan_out(s) for s in scans]

@router.get("/{scan_id}")
def get_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _scan_out(scan)

@router.put("/{scan_id}/status")
def update_status(
    scan_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if status not in ("healthy", "treated", "pending"):
        raise HTTPException(status_code=400, detail="Invalid status")
    scan.status = status
    db.commit()
    return {"message": "Status updated"}

def _scan_out(scan: Scan) -> dict:
    return {
        "id": scan.id,
        "scan_type": scan.scan_type,
        "crop_name": scan.crop_name,
        "health_score": scan.health_score,
        "disease": scan.disease,
        "severity": scan.severity,
        "findings": scan.findings,
        "treatment": scan.treatment,
        "soil_data": scan.soil_data,
        "ai_summary": scan.ai_summary,
        "status": scan.status,
        "location": scan.location,
        "image_url": f"/uploads/{scan.image_path.split('/')[-1]}" if scan.image_path else None,
        "created_at": scan.created_at.isoformat(),
    }