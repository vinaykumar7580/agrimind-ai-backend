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

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_VISION_MODEL: str = "llava"

    CHROMA_PERSIST_DIR: str = "./chroma_db"
    OPENWEATHER_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()