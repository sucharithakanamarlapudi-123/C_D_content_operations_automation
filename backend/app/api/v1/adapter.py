from fastapi import APIRouter, HTTPException
from app.services.adapter_service import AdapterService
from app.schemas.adapter import AdaptationResponse, AdaptationRequest
from pydantic import BaseModel

router = APIRouter()
adapter_service = AdapterService()


@router.post("/adapt", response_model=AdaptationResponse)
async def adapt_content_to_channel(request: AdaptationRequest):
    try:
        # This calls the logic that handles RAG, Channel Rules, and the Change Log
        result = await adapter_service.adapt_content(
            source_content=request.source_content,
            channel=request.channel,
            target_audience=request.target_audience
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Adaptation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to adapt content.")