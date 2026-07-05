from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from models import User
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class SignupRequest(BaseModel):
    name: str
    phone: str
    password: str
    state: Optional[str] = None
    district: Optional[str] = None
    land_acres: Optional[float] = None
    farming_type: Optional[str] = "traditional"
    primary_crops: Optional[List[str]] = []

class LoginRequest(BaseModel):
    phone: str
    password: str

class ResetPasswordRequest(BaseModel):
    phone: str
    new_password: str

@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == req.phone).first():
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = User(
        name=req.name,
        phone=req.phone,
        password_hash=hash_password(req.password),
        state=req.state,
        district=req.district,
        land_acres=req.land_acres,
        farming_type=req.farming_type,
        primary_crops=req.primary_crops,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id})
    return {"message": "Signup completed successfully.", "success":True}

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == req.phone, User.is_active == True).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid mobile number or password")

    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "user": _user_out(user)}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == req.phone, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this mobile number")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "Password reset successfully"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return _user_out(current_user)

@router.put("/me")
def update_profile(
    req: SignupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.name = req.name
    current_user.state = req.state
    current_user.district = req.district
    current_user.land_acres = req.land_acres
    current_user.farming_type = req.farming_type
    current_user.primary_crops = req.primary_crops
    db.commit()
    return _user_out(current_user)

def _user_out(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "state": user.state,
        "district": user.district,
        "land_acres": user.land_acres,
        "farming_type": user.farming_type,
        "primary_crops": user.primary_crops,
        "created_at": user.created_at.isoformat(),
    }