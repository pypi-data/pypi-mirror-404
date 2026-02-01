"""Starvex internal modules - Core engines for high-accuracy detection"""

from .tracer import InternalTracer
from .engine_nemo import NemoEngine
from .engine_eval import EvalEngine

# New semantic engines
try:
    from .semantic_router import SemanticRouter, AccuracyEngine, Route, RouteMatch
except ImportError:
    SemanticRouter = None
    AccuracyEngine = None
    Route = None
    RouteMatch = None

try:
    from .nli_engine import NLIEngine, NLIResult, PolicyChecker
except ImportError:
    NLIEngine = None
    NLIResult = None
    PolicyChecker = None

try:
    from .pii_engine import PIIEngine, PIIGuard, PIIEntity, PIIResult
except ImportError:
    PIIEngine = None
    PIIGuard = None
    PIIEntity = None
    PIIResult = None

__all__ = [
    # Core engines
    "InternalTracer",
    "NemoEngine",
    "EvalEngine",
    # Semantic routing
    "SemanticRouter",
    "AccuracyEngine",
    "Route",
    "RouteMatch",
    # NLI
    "NLIEngine",
    "NLIResult",
    "PolicyChecker",
    # PII
    "PIIEngine",
    "PIIGuard",
    "PIIEntity",
    "PIIResult",
]
