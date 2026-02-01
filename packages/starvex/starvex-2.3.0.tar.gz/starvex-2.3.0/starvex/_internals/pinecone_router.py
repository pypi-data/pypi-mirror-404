"""
Starvex Cloud Router - Cloud-based semantic routing via Starvex API.

Uses Starvex's cloud infrastructure for semantic routing without requiring
users to manage their own Pinecone API keys.

This provides:
- Scalable cloud-based semantic matching
- No local GPU/CPU overhead for embeddings
- Built-in reranking for higher accuracy
- Managed by Starvex - users only need their Starvex API key
"""

import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

httpx = None
requests = None

try:
    import httpx as _httpx

    httpx = _httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import requests as _requests

    requests = _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)

# Starvex API endpoint for semantic routing
STARVEX_API_URL = os.environ.get(
    "STARVEX_API_URL", "https://decqadhkqnacujoyirkh.supabase.co/functions/v1"
)


@dataclass
class RouteMatch:
    """Result of a semantic route match"""

    route: Optional[str]
    score: float
    matched: bool
    details: Dict[str, Any] = field(default_factory=dict)


class CloudSemanticRouter:
    """
    Semantic router using Starvex's cloud API.

    This router calls Starvex's managed semantic routing service,
    which uses Pinecone under the hood. Users only need their
    Starvex API key - no Pinecone configuration required.

    Example:
        router = CloudSemanticRouter(api_key="sk_live_xxx")

        result = router.route("what cryptocurrency should I buy?")
        # result.route == "investment_advice"
        # result.matched == True
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        namespace: str = "default-routes",
        base_url: Optional[str] = None,
    ):
        """
        Initialize the Cloud Semantic Router.

        Args:
            api_key: Starvex API key (or set STARVEX_API_KEY env var)
            namespace: Namespace for semantic routes (default: "default-routes")
            base_url: Override the Starvex API URL (optional)
        """
        self.api_key = api_key or os.environ.get("STARVEX_API_KEY")
        self.namespace = namespace
        self.base_url = base_url or STARVEX_API_URL
        self._endpoint = f"{self.base_url}/semantic-route"

        if not self.api_key:
            logger.warning(
                "No Starvex API key provided. "
                "Set STARVEX_API_KEY env var or pass api_key parameter."
            )

    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Starvex API"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key or "",
        }

        if HAS_HTTPX and httpx is not None:
            with httpx.Client(timeout=30.0) as client:  # type: ignore
                response = client.post(
                    self._endpoint,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        elif HAS_REQUESTS and requests is not None:
            response = requests.post(  # type: ignore
                self._endpoint,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        else:
            raise ImportError(
                "No HTTP client available. Install httpx or requests: pip install httpx"
            )

    def route(
        self,
        text: str,
        top_k: int = 5,
        rerank: bool = True,
    ) -> RouteMatch:
        """
        Route text to the best matching semantic route.

        Args:
            text: Input text to classify
            top_k: Number of candidates to retrieve
            rerank: Whether to use reranking for higher accuracy

        Returns:
            RouteMatch with route name, score, and match status
        """
        if not self.api_key:
            return RouteMatch(
                route=None,
                score=0.0,
                matched=False,
                details={"error": "No API key configured"},
            )

        try:
            result = self._make_request(
                {
                    "text": text,
                    "namespace": self.namespace,
                    "top_k": top_k,
                    "rerank": rerank,
                }
            )

            return RouteMatch(
                route=result.get("route"),
                score=result.get("score", 0.0),
                matched=result.get("matched", False),
                details=result.get("details", {}),
            )

        except Exception as e:
            logger.error(f"Semantic route API error: {e}")
            return RouteMatch(
                route=None,
                score=0.0,
                matched=False,
                details={"error": str(e)},
            )

    def check_intent(self, text: str) -> Dict[str, Any]:
        """
        Check if text matches any forbidden intents.

        Compatible API with AccuracyEngine.

        Returns:
            Dict with 'safe' boolean and 'reason' if unsafe
        """
        result = self.route(text)

        if result.matched:
            return {
                "safe": False,
                "reason": f"Triggered {result.route} guardrail",
                "route": result.route,
                "confidence": result.score,
                "details": result.details,
            }

        return {"safe": True, "confidence": 1.0 - result.score}


class CloudAccuracyEngine:
    """
    Cloud-based AccuracyEngine using Starvex's semantic routing API.

    Drop-in replacement for the local AccuracyEngine that uses
    Starvex's managed Pinecone infrastructure. Users only need
    their Starvex API key.

    Example:
        engine = CloudAccuracyEngine(api_key="sk_live_xxx")

        result = engine.check_intent("how do I hack into a system?")
        # result["safe"] == False
        # result["route"] == "harmful_content"
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        namespace: str = "default-routes",
    ):
        """
        Initialize the Cloud Accuracy Engine.

        Args:
            api_key: Starvex API key (or set STARVEX_API_KEY env var)
            namespace: Namespace for semantic routes
        """
        self.router = CloudSemanticRouter(
            api_key=api_key,
            namespace=namespace,
        )

    def check_intent(self, text: str) -> Dict[str, Any]:
        """Check if text matches forbidden intents"""
        return self.router.check_intent(text)

    @property
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "engine": "cloud",
            "namespace": self.router.namespace,
            "api_configured": bool(self.router.api_key),
        }


# Backwards compatibility aliases
PineconeRouter = CloudSemanticRouter
PineconeRouteMatch = RouteMatch
