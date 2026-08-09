import io
import pypdf
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.core.security import verify_user_token
from app.agent.ingestion import ingest_user_document
from app.services.db_service import save_user_file, get_user_files

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_real_file(
    file: UploadFile = File(...),
    current_user_id: str = Depends(verify_user_token)
):
    """
    Accepts raw binary files (.pdf or .txt), extracts text, registers metadata
    permanently in our database, and structures partitioned indexes into Qdrant.
    """
    file_content = await file.read()
    filename = file.filename
    extracted_text = ""

    try:
        if filename.endswith(".pdf"):
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        elif filename.endswith(".txt"):
            extracted_text = file_content.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .txt or .pdf files.")

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any meaningful text from this file.")

        # Save metadata permanently in disk-backed database
        saved_record = save_user_file(current_user_id, filename, len(file_content))

        # Ingest text vectors into Qdrant partition and BM25 store
        ingest_user_document(
            user_id=current_user_id,
            document_name=filename,
            raw_text=extracted_text
        )

        return {
            "status": "success", 
            "filename": filename, 
            "message": "File parsed and indexed successfully!",
            "file": saved_record
        }

    except Exception as e:
        print(f"❌ Document processing error: {e}")
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")


@router.get("/list")
async def list_user_documents(current_user_id: str = Depends(verify_user_token)):
    """
    Fetches the historical list of files uploaded by the active user.
    """
    files = get_user_files(current_user_id)
    return files