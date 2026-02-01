"""
Starvex Hybrid Router - Production-Ready Three-Tier Decision System

This module implements a HybridRouter that combines:
1. Deterministic keyword matching (Tier 1) - Zero latency exact matches
2. Semantic routing (Tier 2) - Embedding-based intent detection
3. Confidence guard (Tier 3) - Fallback for low-confidence results

This architecture improves accuracy without expensive fine-tuning by using
a cascading decision approach that leverages both rule-based and ML-based
routing strategies.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HybridRouteResult:
    """Result from the hybrid routing decision"""

    route_name: str
    confidence: float
    tier_used: int  # 1 = keyword, 2 = semantic, 3 = fallback
    tier_name: str  # "deterministic", "semantic", or "confidence_guard"
    matched_keyword: Optional[str] = None
    semantic_scores: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_ambiguous(self) -> bool:
        """Check if result fell through to ambiguous intent"""
        return self.route_name == "ambiguous_intent"


class HybridRouter:
    """
    Three-Tier Hybrid Router for High-Accuracy Intent Detection.

    Combines deterministic keyword matching with semantic understanding
    and confidence-based fallback for maximum accuracy.

    Architecture:

    Tier 1 (Deterministic): Check keyword_map for exact substring matches.
                            If found, return immediately with 0 latency.

    Tier 2 (Semantic):      If no keyword match, use SemanticRouter for
                            embedding-based similarity matching.

    Tier 3 (Confidence):    If semantic score is below threshold,
                            route to "ambiguous_intent" fallback.

    Example:
        router = HybridRouter(
            keyword_map={"invoice": "billing", "refund": "billing"},
            confidence_threshold=0.82
        )

        # Tier 1: Exact keyword match
        result = router.route("Where is my invoice?")
        # -> HybridRouteResult(route_name="billing", tier_used=1)

        # Tier 2: Semantic similarity
        result = router.route("I need help with my payment")
        # -> HybridRouteResult(route_name="billing", tier_used=2)

        # Tier 3: Low confidence fallback
        result = router.route("What's the weather like?")
        # -> HybridRouteResult(route_name="ambiguous_intent", tier_used=3)
    """

    def __init__(
        self,
        keyword_map: Optional[Dict[str, str]] = None,
        confidence_threshold: float = 0.82,
        fallback_route: str = "ambiguous_intent",
        case_sensitive: bool = False,
        hot_fix_patterns_path: Optional[str] = None,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
    ):
        """
        Initialize the HybridRouter.

        Args:
            keyword_map: Dictionary mapping keywords to route names.
                         Example: {"invoice": "billing", "password": "auth"}
            confidence_threshold: Minimum confidence score for semantic routing.
                                  Results below this threshold fall to Tier 3.
                                  Default: 0.82
            fallback_route: Route name for low-confidence results.
                           Default: "ambiguous_intent"
            case_sensitive: Whether keyword matching is case-sensitive.
                           Default: False
            hot_fix_patterns_path: Path to hot_fix_patterns.json file for
                                   loading corrected patterns from auto-fix pipeline.
            model_name: HuggingFace model for semantic embeddings.
            device: Device for ML inference ("cpu" or "cuda").
        """
        self.keyword_map = keyword_map or {}
        self.confidence_threshold = confidence_threshold
        self.fallback_route = fallback_route
        self.case_sensitive = case_sensitive
        self.hot_fix_patterns_path = hot_fix_patterns_path
        self.model_name = model_name
        self.device = device

        # Lazy-load semantic router
        self._semantic_router = None
        self._semantic_initialized = False

        # Load hot-fix patterns if available
        self._hot_fix_patterns: Dict[str, str] = {}
        if hot_fix_patterns_path:
            self._load_hot_fix_patterns(hot_fix_patterns_path)

        # Statistics tracking
        self._stats = {
            "total_queries": 0,
            "tier1_hits": 0,
            "tier2_hits": 0,
            "tier3_fallbacks": 0,
            "hot_fix_hits": 0,
        }

        logger.info(
            f"HybridRouter initialized with {len(self.keyword_map)} keywords, "
            f"threshold={confidence_threshold}"
        )

    def _load_hot_fix_patterns(self, path: str) -> None:
        """Load hot-fix patterns from JSON file"""
        try:
            patterns_file = Path(path)
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    # Extract query -> route mappings
                    for pattern in data.get("patterns", []):
                        query = pattern.get("query", "").lower()
                        route = pattern.get("route")
                        if query and route:
                            self._hot_fix_patterns[query] = route
                logger.info(f"Loaded {len(self._hot_fix_patterns)} hot-fix patterns")
        except Exception as e:
            logger.warning(f"Failed to load hot-fix patterns: {e}")

    def _ensure_semantic_router(self) -> None:
        """Lazy initialization of semantic router"""
        if self._semantic_initialized:
            return

        try:
            from .semantic_router import SemanticRouter
            self._semantic_router = SemanticRouter(
                model_name=self.model_name,
                device=self.device,
            )
            self._semantic_initialized = True
            logger.debug("Semantic router initialized")
        except ImportError as e:
            logger.warning(
                f"Semantic router not available: {e}. "
                "Install with: pip install starvex[semantic]"
            )
            self._semantic_initialized = True  # Mark as attempted

    def add_keyword(self, keyword: str, route: str) -> None:
        """
        Add a keyword -> route mapping for Tier 1 matching.

        Args:
            keyword: The keyword to match (will be matched as substring)
            route: The route name to return when keyword is found
        """
        key = keyword if self.case_sensitive else keyword.lower()
        self.keyword_map[key] = route
        logger.debug(f"Added keyword mapping: '{keyword}' -> '{route}'")

    def add_keywords(self, mappings: Dict[str, str]) -> None:
        """
        Add multiple keyword -> route mappings.

        Args:
            mappings: Dictionary of keyword -> route mappings
        """
        for keyword, route in mappings.items():
            self.add_keyword(keyword, route)

    def add_semantic_route(
        self,
        name: str,
        utterances: List[str],
        sensitivity: float = 0.75,
    ) -> None:
        """
        Add a semantic route for Tier 2 matching.

        Args:
            name: Route name
            utterances: Example phrases that should match this route
            sensitivity: Threshold for matching (0-1)
        """
        self._ensure_semantic_router()
        if self._semantic_router:
            from .semantic_router import Route
            route = Route(name=name, utterances=utterances, sensitivity=sensitivity)
            self._semantic_router.add_route(route)

    def route(self, query: str) -> HybridRouteResult:
        """
        Route a query through the three-tier decision system.

        Args:
            query: The user input to route

        Returns:
            HybridRouteResult with route name, confidence, and tier used
        """
        self._stats["total_queries"] += 1

        # Normalize query for matching
        query_normalized = query if self.case_sensitive else query.lower()

        # ===============================
        # TIER 0: Hot-Fix Pattern Check
        # ===============================
        # Check hot-fix patterns first (from auto-fix pipeline)
        if self._hot_fix_patterns:
            for pattern, route in self._hot_fix_patterns.items():
                if pattern in query_normalized or query_normalized == pattern:
                    self._stats["hot_fix_hits"] += 1
                    logger.debug(f"Tier 0 (hot-fix) match: '{pattern}' -> '{route}'")
                    return HybridRouteResult(
                        route_name=route,
                        confidence=1.0,
                        tier_used=0,
                        tier_name="hot_fix",
                        matched_keyword=pattern,
                        metadata={"source": "hot_fix_patterns"}
                    )

        # ===============================
        # TIER 1: Deterministic Keywords
        # ===============================
        for keyword, route in self.keyword_map.items():
            keyword_check = keyword if self.case_sensitive else keyword.lower()
            if keyword_check in query_normalized:
                self._stats["tier1_hits"] += 1
                logger.debug(f"Tier 1 (keyword) match: '{keyword}' -> '{route}'")
                return HybridRouteResult(
                    route_name=route,
                    confidence=1.0,
                    tier_used=1,
                    tier_name="deterministic",
                    matched_keyword=keyword,
                )

        # ===============================
        # TIER 2: Semantic Routing
        # ===============================
        self._ensure_semantic_router()

        if self._semantic_router:
            try:
                result = self._semantic_router.route(query)

                # Collect all scores for debugging
                semantic_scores = {}
                if result.details and "all_scores" in result.details:
                    for route_name, scores in result.details["all_scores"].items():
                        semantic_scores[route_name] = scores.get("max", 0.0)

                # Check if score meets threshold
                if result.matched and result.score >= self.confidence_threshold:
                    self._stats["tier2_hits"] += 1
                    logger.debug(
                        f"Tier 2 (semantic) match: '{result.name}' "
                        f"with confidence {result.score:.3f}"
                    )
                    return HybridRouteResult(
                        route_name=result.name,
                        confidence=result.score,
                        tier_used=2,
                        tier_name="semantic",
                        semantic_scores=semantic_scores,
                    )

                # ===============================
                # TIER 3: Confidence Guard
                # ===============================
                # Score below threshold - fall through to ambiguous
                self._stats["tier3_fallbacks"] += 1
                logger.debug(
                    f"Tier 3 (confidence guard): score {result.score:.3f} "
                    f"below threshold {self.confidence_threshold}"
                )
                return HybridRouteResult(
                    route_name=self.fallback_route,
                    confidence=result.score,
                    tier_used=3,
                    tier_name="confidence_guard",
                    semantic_scores=semantic_scores,
                    metadata={
                        "best_match": result.name,
                        "best_score": result.score,
                        "threshold": self.confidence_threshold,
                    }
                )

            except Exception as e:
                logger.warning(f"Semantic routing failed: {e}")

        # No semantic router available - fall through to ambiguous
        self._stats["tier3_fallbacks"] += 1
        return HybridRouteResult(
            route_name=self.fallback_route,
            confidence=0.0,
            tier_used=3,
            tier_name="confidence_guard",
            metadata={"reason": "no_semantic_router"}
        )

    def route_with_context(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> HybridRouteResult:
        """
        Route with additional context (e.g., conversation history).

        Args:
            query: The user input to route
            context: Additional context like conversation history

        Returns:
            HybridRouteResult with routing decision
        """
        result = self.route(query)

        # Enrich result with context
        if context:
            result.metadata["context"] = context

            # Check for context-based overrides
            if "previous_route" in context and result.is_ambiguous:
                # Could implement context-aware routing here
                result.metadata["context_hint"] = context["previous_route"]

        return result

    def reload_hot_fix_patterns(self) -> int:
        """
        Reload hot-fix patterns from file.

        Returns:
            Number of patterns loaded
        """
        if self.hot_fix_patterns_path:
            self._hot_fix_patterns.clear()
            self._load_hot_fix_patterns(self.hot_fix_patterns_path)
        return len(self._hot_fix_patterns)

    @property
    def stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        total = self._stats["total_queries"]
        return {
            **self._stats,
            "tier1_rate": (self._stats["tier1_hits"] / total * 100) if total > 0 else 0,
            "tier2_rate": (self._stats["tier2_hits"] / total * 100) if total > 0 else 0,
            "tier3_rate": (self._stats["tier3_fallbacks"] / total * 100) if total > 0 else 0,
            "hot_fix_rate": (self._stats["hot_fix_hits"] / total * 100) if total > 0 else 0,
            "keyword_count": len(self.keyword_map),
            "hot_fix_count": len(self._hot_fix_patterns),
            "confidence_threshold": self.confidence_threshold,
        }

    def reset_stats(self) -> None:
        """Reset routing statistics"""
        self._stats = {
            "total_queries": 0,
            "tier1_hits": 0,
            "tier2_hits": 0,
            "tier3_fallbacks": 0,
            "hot_fix_hits": 0,
        }


# Convenience function for quick setup
def create_hybrid_router(
    keyword_map: Optional[Dict[str, str]] = None,
    semantic_routes: Optional[List[Dict[str, Any]]] = None,
    confidence_threshold: float = 0.82,
    hot_fix_path: Optional[str] = None,
) -> HybridRouter:
    """
    Factory function to create a pre-configured HybridRouter.

    Args:
        keyword_map: Keyword -> route mappings for Tier 1
        semantic_routes: List of semantic route definitions for Tier 2
        confidence_threshold: Threshold for Tier 3 confidence guard
        hot_fix_path: Path to hot_fix_patterns.json

    Returns:
        Configured HybridRouter instance

    Example:
        router = create_hybrid_router(
            keyword_map={
                "invoice": "billing",
                "refund": "billing",
                "password": "auth",
                "login": "auth",
            },
            semantic_routes=[
                {
                    "name": "billing",
                    "utterances": [
                        "I need help with my payment",
                        "Where can I see my charges?",
                        "How do I update my payment method?",
                    ],
                    "sensitivity": 0.75
                },
                {
                    "name": "auth",
                    "utterances": [
                        "I can't log in to my account",
                        "How do I reset my password?",
                        "My account is locked",
                    ],
                    "sensitivity": 0.75
                }
            ],
            confidence_threshold=0.82,
        )
    """
    router = HybridRouter(
        keyword_map=keyword_map,
        confidence_threshold=confidence_threshold,
        hot_fix_patterns_path=hot_fix_path,
    )

    if semantic_routes:
        for route_def in semantic_routes:
            router.add_semantic_route(
                name=route_def["name"],
                utterances=route_def["utterances"],
                sensitivity=route_def.get("sensitivity", 0.75),
            )

    return router
