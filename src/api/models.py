"""
Pydantic Data Models for AmazonHelp Support Platform API
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Customer message text to classify")


class ClassifyResponse(BaseModel):
    intent: str
    confidence: float
    language: str
    conversation_state: str


class RetrievedEvidence(BaseModel):
    conversation_id: str
    customer_message: str
    historical_response: str
    score: float


class AgentRespondRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Customer message text")
    conversation_id: Optional[str] = Field(None, description="Optional conversation context ID")


class AgentRespondResponse(BaseModel):
    intent: str
    confidence: float
    language: str
    conversation_state: str
    auto_handle: bool
    escalation_reason: Optional[str] = None
    draft_reply: str
    retrieved_evidence: List[RetrievedEvidence]
    is_security_alert: bool = False
    priority: str = "standard"


# Aliases for backwards compatibility with earlier endpoints
AnalyzeRequest = AgentRespondRequest
AnalyzeResponse = AgentRespondResponse


class ConversationTurn(BaseModel):
    tweet_id: str
    author_id: str
    speaker: str  # 'customer' or 'AmazonHelp'
    created_at: str
    text: str


class TicketSummary(BaseModel):
    conversation_id: str
    preview: str
    customer_id: str
    created_at: str
    total_turns: int
    status: str  # 'new', 'in_progress', 'ai_drafted', 'awaiting_human', 'resolved'
    intent: str
    priority: str  # 'P0_CRITICAL' or 'standard'
    escalate: bool
    is_security_alert: bool
    language: str


class TicketDetail(BaseModel):
    conversation_id: str
    customer_id: str
    status: str
    intent: str
    priority: str
    escalate: bool
    is_security_alert: bool
    language: str
    turns: List[ConversationTurn]
    ai_analysis: Optional[AgentRespondResponse] = None


class TicketsResponse(BaseModel):
    total: int
    page: int
    limit: int
    tickets: List[TicketSummary]


class DraftReplyRequest(BaseModel):
    conversation_id: str
    draft_text: str = Field(..., min_length=1)
    action: str = Field("approve", description="'approve', 'edit', 'mark_human', 'resolve'")
    notes: Optional[str] = None


class DraftReplyResponse(BaseModel):
    success: bool
    conversation_id: str
    new_status: str
    message: str


class ConfusionMatrixResponse(BaseModel):
    intents: List[str]
    matrix: List[List[int]]
    accuracy: float
    macro_f1: float
    per_intent: List[Dict[str, Any]]
    top_confusion_pairs: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    retrieval_index_loaded: bool
    retrieval_records_count: int
    exclusions_active_count: int
    evaluation_artifacts_ready: bool
    version: str = "1.0.0"
