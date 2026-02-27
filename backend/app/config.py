from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "Data Dreamer"
    DATA_DIR: Path = Path(__file__).resolve().parent / "data"

    TITANIC_DATASET: str =  "titanic.csv"
    GROQ_API_KEY: str
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()


