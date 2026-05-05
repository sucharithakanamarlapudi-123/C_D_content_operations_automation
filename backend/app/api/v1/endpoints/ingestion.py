import os
from fastapi import APIRouter, HTTPException
from app.services.vector_service import VectorService
from app.schemas.ingestion import IngestionRequest, IngestionResponse
from langchain_community.document_loaders import PyMuPDFLoader

router = APIRouter()
vector_service = VectorService()

@router.post("/ingest-by-path", response_model=IngestionResponse)
async def ingest_brand_guidelines_by_path(request: IngestionRequest):
    # 1. Check if the path exists
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found at: {request.file_path}")

    # 2. Check if it's a PDF
    if not request.file_path.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="The provided file path must point to a PDF.")

    # 3. Process the file
    try:
        # Load directly from the provided path
        print("Loading the pdf file")
        loader = PyMuPDFLoader(request.file_path)
        raw_docs = loader.load()
        print("Loaded the pdf file")
        
        # Trigger your production-grade pipeline (Enrich + Embed + Store)
        result = await vector_service.create_vector_store(raw_docs)
        
        return IngestionResponse(
            status="success",
            chunks_processed=result["total_chunks"],
            message=f"Successfully ingested rules from {request.file_path}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG Processing failed: {str(e)}")