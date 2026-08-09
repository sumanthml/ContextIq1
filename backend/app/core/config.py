import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Explicitly load the environment file from the backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(backend_dir, ".env")
load_dotenv(dotenv_path)

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "ContextIq1"
    
    # Core API Keys
    GROQ_API_KEY: str
    COHERE_API_KEY: str
    
    # Qdrant Database Connections
    QDRANT_URL: str
    QDRANT_API_KEY: str
    
    # Supabase Multi-Tenancy Engine
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_JWT_SECRET: str
    
    # Cryptographic Isolation Salt
    TENANT_SALT_KEY: str

    class Config:
        case_sensitive = True

# Instantiate the settings container globally
settings = Settings()