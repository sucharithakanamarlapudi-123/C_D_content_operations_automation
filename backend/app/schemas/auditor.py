from pydantic import BaseModel
from typing import List, Optional

class Violation(BaseModel):
    rule_category: str
    issue_found: str
    citation: str
    suggestion: str

class AuditRequest(BaseModel):
    content_to_audit: str

class AuditResponse(BaseModel):
    score: int
    violations: List[Violation]
    summary: str
    report_saved_at: Optional[str] = None