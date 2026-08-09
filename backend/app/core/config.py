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
    GROQ_API_KEY: str = ""
    COHERE_API_KEY: str = ""
    
    # Qdrant Database Connections
    QDRANT_URL: str = "https://62272be4-801b-49db-b987-785e748eae4c.eu-central-1-0.aws.cloud.qdrant.io"
    QDRANT_API_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6M2M3YzYwZmItNjBkYS00N2Y1LWE1MGItNWI2ODA0YzRlYjM5In0.Cw0qxgcHZfhkjTK6VqWIjUAhMiCqCryy-yoyANfPUfQ"
    
    # Supabase Multi-Tenancy Engine (Optional / Fallback)
    SUPABASE_URL: str = "https://mock.supabase.co"
    SUPABASE_ANON_KEY: str = "mock_anon_key"
    SUPABASE_JWT_SECRET: str = "mock_jwt_secret_12345"
    
    # Cryptographic Isolation Salt
    TENANT_SALT_KEY: str = "MySecretContextIq1Salt99!xYz_SuperSecure12345"

    class Config:
        case_sensitive = True
        extra = "ignore"

# Instantiate the settings container globally
settings = Settings()