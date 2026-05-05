from pydantic import BaseModel, Field
from typing import List, Optional

class ChunkMetadata(BaseModel):
    """Schema for the enriched metadata stored in ChromaDB"""
    source_file: str = Field(..., description="The name of the PDF file")
    page_number: int = Field(..., description="The page number from the PDF")
    section_title: str = Field(..., description="e.g., VOICE AND TONE")
    rule_category: str = Field(..., description="e.g., Banned Word, Terminology, CTA")
    audience_target: Optional[str] = Field(None, description="Executive, Technical, etc.")
    is_violation_rule: bool = Field(True, description="True if this chunk contains a 'do/don't' rule")

class IngestionRequest(BaseModel):
    file_path: str  # e.g., "C:/Documents/Axion_Guidelines.pdf"

class IngestionResponse(BaseModel):
    status: str
    chunks_processed: int
    message: str