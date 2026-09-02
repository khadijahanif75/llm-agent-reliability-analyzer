import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "LLM Agent Trace & Reliability Analyzer"
    ENV: str = "development"
    
    # LLM Settings
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = "mock-agent-v1"
    
    # Execution Constraints
    MAX_STEPS: int = 6
    MAX_RETRIES: int = 2
    
    # Storage Settings
    DATABASE_PATH: Path = BASE_DIR / "data" / "tracer.db"
    
    # Failure Injection
    ENABLE_FAILURE_INJECTION: bool = False
    SEARCH_FAILURE_RATE: float = 0.0
    DATABASE_FAILURE_RATE: float = 0.0
    RANDOM_SEED: int = 42

settings = Settings()