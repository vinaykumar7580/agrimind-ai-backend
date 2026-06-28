from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import User, ChatMessage, Scan
from auth import get_current_user
from agents.orchestrator import chat
import json

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    scan_id: Optional[int] = None

@router.post("/message")
async def send_message(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get conversation history (last 10 messages)
    history = db.query(ChatMessage)\
        .filter(ChatMessage.user_id == current_user.id)\
        .order_by(ChatMessage.created_at.desc())\
        .limit(10).all()
    history_list = [{"role": m.role, "content": m.content} for m in reversed(history)]

    # Get scan context if provided
    scan_context = None
    if req.scan_id:
        scan = db.query(Scan).filter(Scan.id == req.scan_id, Scan.user_id == current_user.id).first()
        if scan:
            scan_context = {
                "crop_name": scan.crop_name,
                "disease": scan.disease,
                "health_score": scan.health_score,
                "severity": scan.severity,
                "ai_summary": scan.ai_summary,
            }

    # User profile context
    user_profile = {
        "state": current_user.state,
        "district": current_user.district,
        "land_acres": current_user.land_acres,
        "farming_type": current_user.farming_type,
        "primary_crops": current_user.primary_crops,
    }

    # Save user message
    user_msg = ChatMessage(user_id=current_user.id, role="user", content=req.message, scan_id=req.scan_id)
    db.add(user_msg)
    db.commit()

    # Generate AI response
    response = await chat(req.message, history_list, scan_context, user_profile)

    # Save AI response
    ai_msg = ChatMessage(user_id=current_user.id, role="assistant", content=response, scan_id=req.scan_id)
    db.add(ai_msg)
    db.commit()

    return {"response": response, "message_id": ai_msg.id}

@router.get("/history")
def get_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = db.query(ChatMessage)\
        .filter(ChatMessage.user_id == current_user.id)\
        .order_by(ChatMessage.created_at.asc())\
        .offset(skip).limit(limit).all()
    return [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in messages]

@router.delete("/history")
def clear_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Chat history cleared"}