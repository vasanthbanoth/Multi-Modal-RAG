from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from backend.app.core.config import Settings, settings
from backend.app.services.embedding import embedding_service, EmbeddingService
from backend.app.services.vector_db import vector_db_service, VectorDBService, KBType
from backend.app.services.parser import document_service, DocumentService
from backend.app.services.storage_service import storage_service, StorageService
from backend.app.services.llm_gen import generative_service, GenerativeService
from backend.app.services.rag_pipeline import RAGPipelineService
from backend.app.api.v1.auth import get_current_active_user
from backend.app.api.v1 import schemas
from PIL import Image
import hashlib
import io

router = APIRouter()

@router.get("/", response_model=schemas.HealthCheck)
def home(app_settings: Settings = Depends(lambda: settings)):
    return {"message": "I am the medical chatbot!.how can i help you?", "google_api_key_loaded": bool(app_settings.GOOGLE_API_KEY)}

@router.post("/embeddings/", response_model=schemas.EmbeddingResponse)
async def create_embedding(
    text: str | None = Form(None),
    image: UploadFile | None = File(None),
    kb_type: KBType = Form(KBType.GKB),
    current_user: schemas.User = Depends(get_current_active_user),
    embed_service: EmbeddingService = Depends(lambda: embedding_service),
    db_service: VectorDBService = Depends(lambda: vector_db_service),
    store_service: StorageService = Depends(lambda: storage_service),
):
    """
    Creates a vector embedding and upserts it into the appropriate knowledge base (GKB or SKB).

    - **kb_type**: 'gkb' for General Knowledge Base or 'skb' for Specific Knowledge Base.
    - **context_id**: Required if kb_type is 'skb'. This isolates the knowledge (e.g., to a user).
    - Provide either 'text' or 'image' form data.
    """
    if not text and not image:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide either 'text' or 'image'.")
    
    context_id = None
    if kb_type == KBType.SKB:
        context_id = current_user.email
    if kb_type == KBType.SKB and not context_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A 'context_id' is required for SKB operations.")
    
    embedding = None
    source_type = ""
    source_id = ""

    try:
        if text:
            source_type = "text"
            object_name = f"text/{context_id or 'gkb'}/{hashlib.md5(text.encode()).hexdigest()}.txt"
            source_id = f"s3://{store_service.bucket_name}/{object_name}"
            
            if not store_service.upload_file(io.BytesIO(text.encode('utf-8')), object_name):
                raise HTTPException(status_code=500, detail="Failed to upload text to cloud storage.")

            embedding = embed_service.create_text_embedding(text)
        elif image:
            source_type = "image"
            object_name = f"images/{context_id or 'gkb'}/{image.filename or 'unknown'}"
            source_id = f"s3://{store_service.bucket_name}/{object_name}"
            
            contents = await image.read()
            file_stream = io.BytesIO(contents)
            
            if not store_service.upload_file(file_stream, object_name):
                raise HTTPException(status_code=500, detail="Failed to upload image to cloud storage.")
            
            # Reset the stream's position to the beginning before reading it again for PIL
            file_stream.seek(0)
            pil_image = Image.open(file_stream)
            embedding = embed_service.create_image_embedding(pil_image)

        vector_id = db_service.upsert(embedding, kb_type, source_type, source_id, context_id)
        return {"status": "success", "vector_id": vector_id, "kb_type": kb_type, "context_id": context_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

@router.post("/documents/extract/", response_model=schemas.ExtractionResponse)
async def extract_from_document(
    file: UploadFile = File(...),
    doc_service: DocumentService = Depends(lambda: document_service)
):
    """
    Extracts text and images from an uploaded document (currently supports PDF).
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type. Please upload a PDF.")

    try:
        contents = await file.read()
        file_stream = io.BytesIO(contents)
        
        text, images = doc_service.extract_from_pdf(file_stream)
        return {"filename": file.filename, "text_length": len(text), "image_count": len(images)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process PDF: {e}") from e

@router.post("/query/", response_model=schemas.QueryResponse)
async def perform_query(
    query: str = Form(...),
    kb_type: KBType = Form(KBType.GKB),
    current_user: schemas.User = Depends(get_current_active_user),
    embed_service: EmbeddingService = Depends(lambda: embedding_service),
    db_service: VectorDBService = Depends(lambda: vector_db_service),
    store_service: StorageService = Depends(lambda: storage_service),
    gen_service: GenerativeService = Depends(lambda: generative_service),
):
    """
    Performs a full RAG query:
    Orchestrates the RAG pipeline to retrieve context and generate a final answer.
    """
    try:
        context_id = None
        if kb_type == KBType.SKB:
            context_id = current_user.email

        # Initialize the pipeline service with all its dependencies
        pipeline = RAGPipelineService(
            embedding_service=embed_service,
            vector_db_service=db_service,
            storage_service=store_service,
            generative_service=gen_service,
        )
        # Run the pipeline
        result = pipeline.run_pipeline(query, kb_type, context_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e