from supabase import create_client, Client
from app.core.config import settings

try:
    # Initialize the remote Supabase client container using our verified Pydantic credentials
    supabase_client: Client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_ANON_KEY
    )
    print("✅ Supabase cloud service client successfully initialized!")
    
except Exception as e:
    print(f"❌ Failed to initialize Supabase connection wrapper: {str(e)}")
    raise e