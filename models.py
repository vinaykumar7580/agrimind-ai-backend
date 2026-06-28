from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(120), nullable=False)
    phone         = Column(String(15), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    state         = Column(String(60))
    district      = Column(String(60))
    land_acres    = Column(Float, default=0)
    farming_type  = Column(Enum("traditional", "organic", "modern"), default="traditional")
    primary_crops = Column(JSON)          # list of strings
    created_at    = Column(DateTime, default=datetime.utcnow)
    is_active     = Column(Boolean, default=True)

    scans    = relationship("Scan", back_populates="user", cascade="all, delete")
    messages = relationship("ChatMessage", back_populates="user", cascade="all, delete")
    posts    = relationship("CommunityPost", back_populates="user", cascade="all, delete")


class Scan(Base):
    __tablename__ = "scans"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    scan_type    = Column(Enum("crop", "soil"), nullable=False)
    image_path   = Column(String(512))
    crop_name    = Column(String(120))
    crop_variety = Column(String(120))
    health_score = Column(Integer)
    disease      = Column(String(255))
    severity     = Column(Enum("none", "low", "medium", "high"))
    findings     = Column(JSON)           # list of {label, desc, type}
    treatment    = Column(JSON)           # list of {step, action, urgent}
    soil_data    = Column(JSON)           # NPK, pH, moisture etc.
    ai_summary   = Column(Text)
    status       = Column(Enum("healthy", "treated", "pending"), default="pending")
    location     = Column(String(120))
    created_at   = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scans")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    role       = Column(Enum("user", "assistant"), nullable=False)
    content    = Column(Text, nullable=False)
    scan_id    = Column(Integer, ForeignKey("scans.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="messages")


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    title      = Column(String(255), nullable=False)
    body       = Column(Text, nullable=False)
    tag        = Column(String(60))
    emoji      = Column(String(10))
    image_path = Column(String(512))
    post_tags  = Column(JSON)             # list of strings
    likes      = Column(Integer, default=0)
    comments   = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="posts")


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id         = Column(Integer, primary_key=True, index=True)
    crop_name  = Column(String(120), index=True)
    variety    = Column(String(120))
    price      = Column(Float)
    prev_price = Column(Float)
    msp        = Column(Float, nullable=True)
    market     = Column(String(120))
    state      = Column(String(60))
    category   = Column(String(60))
    recorded_at = Column(DateTime, default=datetime.utcnow)


class WeatherLog(Base):
    __tablename__ = "weather_logs"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=True)
    district     = Column(String(60))
    state        = Column(String(60))
    temp_c       = Column(Float)
    humidity     = Column(Integer)
    wind_kmh     = Column(Float)
    rain_chance  = Column(Integer)
    condition    = Column(String(120))
    forecast     = Column(JSON)           # 7-day list
    advisory     = Column(Text)
    recorded_at  = Column(DateTime, default=datetime.utcnow)