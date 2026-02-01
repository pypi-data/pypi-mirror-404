"""
Starvex Models - Pydantic models for inputs/outputs
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class GuardVerdict(str, Enum):
    """Verdict types for guard checks"""

    PASSED = "PASSED"
    BLOCKED_JAILBREAK = "BLOCKED_JAILBREAK"
    BLOCKED_PII = "BLOCKED_PII"
    BLOCKED_TOXICITY = "BLOCKED_TOXICITY"
    BLOCKED_COMPETITOR = "BLOCKED_COMPETITOR"
    BLOCKED_CUSTOM = "BLOCKED_CUSTOM"
    BLOCKED_TOPIC = "BLOCKED_TOPIC"  # Semantic router topic block
    FAILED_HALLUCINATION = "FAILED_HALLUCINATION"
    FAILED_SYSTEM = "FAILED_SYSTEM"


class GuardRuleType(str, Enum):
    """Types of guard rules"""

    JAILBREAK = "jailbreak"
    PII = "pii"
    TOXICITY = "toxicity"
    COMPETITOR = "competitor"
    HALLUCINATION = "hallucination"
    CUSTOM = "custom"
    TOPIC = "topic"  # Semantic router topic detection


class GuardRule(BaseModel):
    """Configuration for a guard rule"""

    rule_type: GuardRuleType
    enabled: bool = True
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    custom_patterns: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class GuardConfig(BaseModel):
    """Full configuration for Starvex"""

    rules: List[GuardRule] = Field(default_factory=list)
    redact_pii: bool = False
    log_level: str = "INFO"
    api_host: str = "https://decqadhkqnacujoyirkh.supabase.co/functions/v1"
    timeout_seconds: int = 30


class GuardInput(BaseModel):
    """Input for guard check"""

    prompt: str
    context: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GuardCheckResult(BaseModel):
    """Result of a single guard check"""

    rule_type: GuardRuleType
    passed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class GuardResponse(BaseModel):
    """Full response from Starvex"""

    status: str  # "success", "blocked", "flagged"
    response: Optional[str] = None
    verdict: GuardVerdict
    checks: List[GuardCheckResult] = Field(default_factory=list)
    trace_id: str
    latency_ms: float
    warning: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TraceEvent(BaseModel):
    """Event to be logged to the tracer"""

    trace_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    input_text: str
    output_text: Optional[str] = None
    verdict: GuardVerdict
    confidence_score: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    latency_ms: float
    metadata: Optional[Dict[str, Any]] = None


class EvalMetrics(BaseModel):
    """Evaluation metrics"""

    hallucination_score: float = Field(ge=0.0, le=1.0)
    faithfulness_score: float = Field(ge=0.0, le=1.0)
    relevancy_score: float = Field(ge=0.0, le=1.0)
    toxicity_score: float = Field(ge=0.0, le=1.0)
    bias_score: float = Field(ge=0.0, le=1.0)


# API Models for Backend
class APIKeyInfo(BaseModel):
    """API Key information"""

    key_id: str
    prefix: str  # e.g., "sv_live_"
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    rate_limit: int = 10000  # requests per month
    is_active: bool = True


class UsageStats(BaseModel):
    """Usage statistics"""

    total_requests: int
    blocked_requests: int
    passed_requests: int
    flagged_requests: int
    hallucination_rate: float
    jailbreak_attempts: int
    pii_blocked: int
    avg_latency_ms: float


class SemanticRouteConfig(BaseModel):
    """Configuration for a semantic route from dashboard"""

    name: str
    description: Optional[str] = None
    utterances: List[str] = Field(default_factory=list)
    sensitivity: float = Field(default=0.75, ge=0.0, le=1.0)
    action: str = "block"  # "block", "flag", "allow"
    enabled: bool = True
    is_default: bool = False
    auto_generated: bool = False


class DashboardConfig(BaseModel):
    """Configuration from dashboard"""

    block_competitor_names: bool = False
    block_pii: bool = True
    block_toxicity: bool = True
    jailbreak_threshold: float = 0.7
    hallucination_threshold: float = 0.5
    competitor_names: List[str] = Field(default_factory=list)
    custom_blocked_phrases: List[str] = Field(default_factory=list)
    semantic_routes: List[SemanticRouteConfig] = Field(default_factory=list)
