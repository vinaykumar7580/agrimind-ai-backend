from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_SECRET_KEY: str = "changeme"
    APP_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "agrimind"
    MYSQL_SSL: bool = False   # cloud MySQL (TiDB Cloud, Aiven) requires True

    # Comma-separated origins allowed to call the API, e.g. your Vercel URL
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    GEMINI_VISION_MODEL: str = "gemini-3.6-flash"
    GEMINI_EMBED_MODEL: str = "gemini-embedding-001"

    OPENWEATHER_API_KEY: str = ""
    DATA_GOV_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()