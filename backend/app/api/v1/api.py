from fastapi import APIRouter
from app.api.v1.endpoints import ingestion, auditor, adapter

api_router = APIRouter()

# Registering the ingestion endpoint under the 'brand' tag
api_router.include_router(ingestion.router, prefix="/brand", tags=["Brand Ingestion"])
api_router.include_router(auditor.router, prefix="/audit", tags=["Brand Auditor"])
api_router.include_router(adapter.router, prefix="/adapter", tags=["Content Adapter"])