from typing import Optional, List
from pydantic import BaseModel

from app.schemas import BaseSerializer


class ChatMessage(BaseSerializer):
    session_id: Optional[str] = None
    message: str


class PredictionResult(BaseModel):
    has_pcos: bool
    confidence: float
    risk_level: str
    recommendations: List[str]


class ProgressInfo(BaseModel):
    current_step: int
    total_steps: int
    percentage: int


class ChatResponse(BaseSerializer):
    session_id: str
    message: str
    step: int
    progress: ProgressInfo
    finished: bool
    prediction: Optional[PredictionResult] = None