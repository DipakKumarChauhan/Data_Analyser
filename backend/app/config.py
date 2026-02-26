from pydantic import BaseSettings
from Pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str
    DATA_DIR: Path = Path(__file__).resolve().parent / "data"

    TITANIC_DATASET: str =  "titanic.csv"
    GROQ_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()


