from pydantic import BaseModel
from typing import List

class ChangeLogEntry(BaseModel):
    original_element: str
    adapted_element: str
    rationale: str

class AdaptationResponse(BaseModel):
    channel: str
    target_audience: str
    adapted_content: str
    change_log: List[ChangeLogEntry]
    brand_compliance_check: str # Brief note on how it followed brand rules

class AdaptationRequest(BaseModel):
    source_content: str
    channel: str # e.g., "linkedin", "sdr_email", "landing_page"
    target_audience: str
