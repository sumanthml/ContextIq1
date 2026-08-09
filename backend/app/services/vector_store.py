from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings

def get_qdrant_client() -> QdrantClient:
    try:
        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        client.get_collections()
        print("⚡ Successfully connected to Qdrant Cloud cluster.")
        return client
    except Exception as err:
        print(f"⚠️ Remote Qdrant Cloud cluster unreachable ({err}). Falling back to local persistent Qdrant store.")
        return QdrantClient(path="./qdrant_storage")

qdrant_client = get_qdrant_client()

def init_vector_collection(collection_name: str = "contextiq_knowledge"):
    """
    Checks if our custom knowledge collection exists in Qdrant Cloud / In-memory store.
    Provisions hardware settings and indexes payload metrics to isolate data safely.
    """
    try:
        # Check if the collection already exists in the cluster
        exists = qdrant_client.collection_exists(collection_name=collection_name)
        
        if not exists:
            print(f"🚀 Vector collection '{collection_name}' not found. Initializing...")
            
            # 1. Create the collection with optimized settings for Cohere v3 embeddings
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=1024,  # Dimensionality matching cohere/embed-english-v3.0
                    distance=models.Distance.COSINE # The optimal math formula for text matching
                ),
            )
            print(f"✅ Vector collection '{collection_name}' successfully created!")
            
        # 2. Secure multi-tenant payload 'tenant_owner' keyword index
        try:
            qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="tenant_owner",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            print("✅ Secure multi-tenant payload 'tenant_owner' keyword index verified.")
        except Exception as index_err:
            print(f"ℹ️ Tenant owner index check status: {str(index_err)}")
            
        # 3. Secure document-scoping payload 'file_name' keyword index
        try:
            qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="file_name",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            print("✅ Secure document-scoping payload 'file_name' keyword index established.")
        except Exception as file_index_err:
            print(f"ℹ️ File name index check status: {str(file_index_err)}")
            
        # 4. Secure document-scoping payload 'document_name' keyword index
        try:
            qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="document_name",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            print("✅ Secure document-scoping payload 'document_name' keyword index established!")
        except Exception as doc_index_err:
            print(f"ℹ️ Document name index check status: {str(doc_index_err)}")
            
        print(f"✨ Vector collection '{collection_name}' is online, fully indexed, and ready.")
            
    except Exception as e:
        print(f"❌ Error setting up vector collection: {str(e)}")
        raise e