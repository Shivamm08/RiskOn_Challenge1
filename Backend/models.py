"""Pydantic models mirroring src/lib/suitability/types.ts exactly.
Context uses camelCase (bookingCentre, clientCategory, serviceModel) to match
the frontend's QueryContext type — everything else follows the original
API_CONTRACT.md snake_case convention, matching AskResponse in types.ts.
"""
from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


BookingCentre = Literal["CH", "Monaco", "Germany", "EEA", "Other"]
ClientCategory = Literal["Private/Retail", "Professional", "Institutional"]
ServiceModel = Literal["Advisory", "Execution-only", "Portfolio Management"]
ResponseStatus = Literal["answered", "escalated", "clarification_needed"]
EscalationTier = Literal[
    "suitability_champion", "business_front_support", "expert",
    "senior_expert", "brm_suitability_lead",
]
SourceFileType = Literal["link", "excel", "csv", "doc", "pdf"]


class QueryContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_centre: Optional[BookingCentre] = Field(default=None, alias="bookingCentre")
    client_category: Optional[ClientCategory] = Field(default=None, alias="clientCategory")
    service_model: Optional[ServiceModel] = Field(default=None, alias="serviceModel")


class AskRequest(BaseModel):
    question: str
    context: QueryContext = QueryContext()
    rm_name: Optional[str] = None


class Confidence(BaseModel):
    answer_confidence: float = 0.0
    routing_confidence: float = 0.0


class SourceRef(BaseModel):
    page_title: str
    excerpt: str
    url: Optional[str] = None
    fileType: Optional[SourceFileType] = None
    source_type: Optional[Literal["wiki", "chat_kb"]] = "wiki"
    trust_score: Optional[float] = None


class Expert(BaseModel):
    name: str
    role: str
    team: str


class FallbackContact(BaseModel):
    name: str
    role: str


class Escalation(BaseModel):
    required: bool = False
    tier: EscalationTier = "suitability_champion"
    expert: Optional[Expert] = None
    reason: str = ""
    fallback_contact: Optional[FallbackContact] = None


class AskResponse(BaseModel):
    request_id: str
    status: ResponseStatus
    answer: Optional[str] = None
    confidence: Confidence = Confidence()
    sources: list[SourceRef] = []
    scope_flags: list[str] = []
    escalation: Optional[Escalation] = None
    clarification_question: Optional[str] = None
    reasoning: Optional[list[str]] = None
    quick_replies: Optional[list[str]] = None


class FeedbackRequest(BaseModel):
    request_id: str
    resolved_by: str
    final_answer: str
    was_ai_correct: bool


class FeedbackResponse(BaseModel):
    status: str
