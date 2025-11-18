# models.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class EmailCategory(str, Enum):
    PRODUTIVO = "PRODUTIVO"
    IMPRODUTIVO = "IMPRODUTIVO"


class EmailRequest(BaseModel):
    text: Optional[str] = Field(None, description="Texto direto do email")
    file_content: Optional[str] = Field(None, description="Conteúdo de arquivo processado")

    model_config = {
        "protected_namespaces": ()
    }


class ClassificationResult(BaseModel):
    category: EmailCategory
    confidence: float = Field(..., ge=0, le=1)
    suggested_response: str
    processing_time: float
    model_used: str
    tokens_processed: Optional[int] = None
    detected_topics: Optional[List[str]] = None

    model_config = {
        "protected_namespaces": ()
    }


class HealthCheck(BaseModel):
    status: str
    timestamp: str
    model_status: str
    version: str

    model_config = {
        "protected_namespaces": ()
    }


class APIResponse(BaseModel):
    status: str
    data: Optional[ClassificationResult] = None
    error: Optional[str] = None
    message: Optional[str] = None

    model_config = {
        "protected_namespaces": ()
    }


class PerformanceMetrics(BaseModel):
    total_requests: int
    successful_classifications: int
    average_processing_time: float
    error_count: int

    model_config = {
        "protected_namespaces": ()
    }