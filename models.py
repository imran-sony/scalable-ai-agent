from enum import Enum
from pydantic import BaseModel
from typing import Optional


class InputType(str, Enum):
    PDF = "pdf"
    TEXT = "text"


class AnalysisRequest(BaseModel):
    input_type: InputType
    content: str
    prompt: Optional[str] = None


class AnalysisResponse(BaseModel):
    task_id: str
    summary: Optional[str] = None
    status: Optional[str] = None
