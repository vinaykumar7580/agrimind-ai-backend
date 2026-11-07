from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

# URL.create keeps special characters in the password (like @) from breaking the URL.
DATABASE_URL = URL.create(
    "mysql+pymysql",
    username=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    host=settings.MYSQL_HOST,
    port=settings.MYSQL_PORT,
    database=settings.MYSQL_DATABASE,
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables."""
    from models import User, Scan, ChatMessage, CommunityPost, MarketPrice, WeatherLog
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")