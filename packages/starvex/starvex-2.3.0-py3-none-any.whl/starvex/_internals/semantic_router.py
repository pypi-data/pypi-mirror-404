"""
Starvex Semantic Router - High-Accuracy Intent Detection
Uses vector embeddings for semantic understanding instead of regex matching.
"""

import logging
import hashlib
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Route:
    """
    A semantic route representing a topic/intent to detect.

    Example:
        politics = Route(
            name="politics",
            utterances=[
                "who should I vote for?",
                "democrat or republican?",
                "is the president good?",
            ],
            sensitivity=0.75
        )
    """

    name: str
    utterances: List[str]
    sensitivity: float = 0.75  # Threshold for matching (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _embeddings: Optional[np.ndarray] = field(default=None, repr=False)


@dataclass
class RouteMatch:
    """Result of a semantic route match"""

    name: Optional[str]
    score: float
    matched: bool
    details: Dict[str, Any] = field(default_factory=dict)


class SemanticRouter:
    """
    Semantic Router for high-accuracy intent/topic detection.

    Uses sentence embeddings to understand meaning, not just keywords.
    This catches semantic variations like:
    - "Where should I put my money?" -> matches "Investment Advice"
    - "Is AWS better?" -> matches "Competitors"

    Example:
        router = SemanticRouter()
        router.add_route(Route(
            name="politics",
            utterances=["who should I vote for?", "political opinion"],
            sensitivity=0.75
        ))

        result = router.route("what do you think about the election?")
        # result.name == "politics", result.matched == True
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        cache_embeddings: bool = True,
    ):
        """
        Initialize the Semantic Router.

        Args:
            model_name: HuggingFace sentence-transformers model name
            device: Device to run model on ("cpu" or "cuda")
            cache_embeddings: Whether to cache embeddings for performance
        """
        self.model_name = model_name
        self.device = device
        self.cache_embeddings = cache_embeddings

        self._encoder = None
        self._routes: Dict[str, Route] = {}
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of the encoder"""
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer

            self._encoder = SentenceTransformer(self.model_name, device=self.device)
            self._initialized = True
            logger.info(f"SemanticRouter initialized with model: {self.model_name}")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. Install with: pip install starvex[semantic]"
            )
            raise ImportError(
                "SemanticRouter requires sentence-transformers. "
                "Install with: pip install starvex[semantic]"
            )

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()

    def _encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings with caching"""
        self._ensure_initialized()

        if not self.cache_embeddings:
            return self._encoder.encode(texts, convert_to_numpy=True)

        # Check cache
        embeddings = []
        texts_to_encode = []
        text_indices = []

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                embeddings.append((i, self._embedding_cache[cache_key]))
            else:
                texts_to_encode.append(text)
                text_indices.append(i)

        # Encode uncached texts
        if texts_to_encode:
            new_embeddings = self._encoder.encode(texts_to_encode, convert_to_numpy=True)
            for idx, (orig_idx, text) in enumerate(zip(text_indices, texts_to_encode)):
                cache_key = self._get_cache_key(text)
                self._embedding_cache[cache_key] = new_embeddings[idx]
                embeddings.append((orig_idx, new_embeddings[idx]))

        # Sort by original index and return
        embeddings.sort(key=lambda x: x[0])
        return np.array([e[1] for e in embeddings])

    def add_route(self, route: Route) -> None:
        """
        Add a route to the router.

        Args:
            route: Route object with name, utterances, and sensitivity
        """
        self._ensure_initialized()

        # Pre-compute embeddings for route utterances
        route._embeddings = self._encode(route.utterances)
        self._routes[route.name] = route

        logger.debug(f"Added route '{route.name}' with {len(route.utterances)} utterances")

    def remove_route(self, name: str) -> bool:
        """Remove a route by name"""
        if name in self._routes:
            del self._routes[name]
            return True
        return False

    def route(self, text: str) -> RouteMatch:
        """
        Route text to the best matching route.

        Args:
            text: Input text to classify

        Returns:
            RouteMatch with name, score, and whether it matched above threshold
        """
        if not self._routes:
            return RouteMatch(name=None, score=0.0, matched=False)

        self._ensure_initialized()

        # Encode input
        text_embedding = self._encode([text])[0]

        best_match = None
        best_score = 0.0
        all_scores = {}

        for route_name, route in self._routes.items():
            # Compute cosine similarity with all route utterances
            similarities = self._cosine_similarity(text_embedding, route._embeddings)
            max_similarity = float(np.max(similarities))
            avg_similarity = float(np.mean(similarities))

            # Use max similarity as the score
            score = max_similarity
            all_scores[route_name] = {
                "max": max_similarity,
                "avg": avg_similarity,
                "threshold": route.sensitivity,
            }

            if score > best_score:
                best_score = score
                best_match = route_name

        # Check if best match exceeds threshold
        matched = False
        if best_match and best_score >= self._routes[best_match].sensitivity:
            matched = True
        else:
            best_match = None

        return RouteMatch(
            name=best_match,
            score=best_score,
            matched=matched,
            details={"all_scores": all_scores},
        )

    def route_multi(self, text: str) -> List[RouteMatch]:
        """
        Route text and return all routes above their thresholds.

        Args:
            text: Input text to classify

        Returns:
            List of RouteMatch objects for all matching routes
        """
        if not self._routes:
            return []

        self._ensure_initialized()

        # Encode input
        text_embedding = self._encode([text])[0]

        matches = []

        for route_name, route in self._routes.items():
            similarities = self._cosine_similarity(text_embedding, route._embeddings)
            max_similarity = float(np.max(similarities))

            if max_similarity >= route.sensitivity:
                matches.append(
                    RouteMatch(
                        name=route_name,
                        score=max_similarity,
                        matched=True,
                        details={"utterance_scores": similarities.tolist()},
                    )
                )

        # Sort by score descending
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between vector a and matrix b"""
        # Normalize
        a_norm = a / (np.linalg.norm(a) + 1e-8)
        b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)

        return np.dot(b_norm, a_norm)

    def clear_cache(self):
        """Clear the embedding cache"""
        self._embedding_cache.clear()

    @property
    def routes(self) -> List[str]:
        """Get list of route names"""
        return list(self._routes.keys())

    @property
    def stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        return {
            "model": self.model_name,
            "num_routes": len(self._routes),
            "total_utterances": sum(len(r.utterances) for r in self._routes.values()),
            "cache_size": len(self._embedding_cache),
            "initialized": self._initialized,
        }


class AccuracyEngine:
    """
    High-Accuracy Detection Engine for Starvex.

    Combines:
    1. Semantic Router - For topic/intent detection using embeddings
    2. NLI Check - For logical consistency verification
    3. PII Detection - Using Microsoft Presidio

    This is the "brain" of Starvex that makes it accurate for agentic systems.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
    ):
        """
        Initialize the AccuracyEngine.

        Args:
            model_name: Embedding model for semantic routing
            device: Device to run models on
        """
        self.router = SemanticRouter(model_name=model_name, device=device)
        self._setup_default_routes()

    def _setup_default_routes(self):
        """Setup default forbidden routes"""
        # Politics route
        politics = Route(
            name="politics",
            utterances=[
                "who should I vote for?",
                "democrat or republican?",
                "is the president good?",
                "political opinion",
                "what party do you support?",
                "tell me about the election",
                "liberal or conservative?",
                "government policy opinion",
                "what do you think of the senator?",
                "support this political candidate",
            ],
            sensitivity=0.72,
        )

        # Competitor route
        competitors = Route(
            name="competitors",
            utterances=[
                "is AWS better?",
                "compare with Google Cloud",
                "why are you expensive?",
                "how do you compare to competitors?",
                "should I use OpenAI instead?",
                "what about Anthropic Claude?",
                "is ChatGPT better than you?",
                "Microsoft Copilot vs this",
                "competitor pricing comparison",
            ],
            sensitivity=0.70,
        )

        # Investment/Financial advice route
        investment = Route(
            name="investment_advice",
            utterances=[
                "where should I invest my money?",
                "should I buy bitcoin?",
                "is this stock a good buy?",
                "financial advice for my portfolio",
                "which cryptocurrency should I buy?",
                "invest in real estate or stocks?",
                "retirement investment strategy",
                "how to make money fast",
            ],
            sensitivity=0.73,
        )

        # Medical advice route
        medical = Route(
            name="medical_advice",
            utterances=[
                "what medication should I take?",
                "diagnose my symptoms",
                "is this medicine safe?",
                "medical treatment recommendation",
                "should I see a doctor about this?",
                "what disease do I have?",
                "prescription drug advice",
            ],
            sensitivity=0.75,
        )

        # Legal advice route
        legal = Route(
            name="legal_advice",
            utterances=[
                "is this legal?",
                "what are my legal rights?",
                "should I sue them?",
                "legal advice for my case",
                "can I be prosecuted for this?",
                "contract legal review",
                "lawyer recommendation for lawsuit",
            ],
            sensitivity=0.74,
        )

        # Add all default routes
        for route in [politics, competitors, investment, medical, legal]:
            try:
                self.router.add_route(route)
            except ImportError:
                logger.warning(
                    f"Could not add route {route.name} - semantic dependencies not available"
                )
                break

    def add_custom_route(
        self,
        name: str,
        utterances: List[str],
        sensitivity: float = 0.75,
    ) -> None:
        """
        Add a custom route for topic detection.

        Args:
            name: Name of the route (e.g., "competitors", "politics")
            utterances: Example phrases that should match this route
            sensitivity: Threshold for matching (0-1, higher = stricter)
        """
        route = Route(name=name, utterances=utterances, sensitivity=sensitivity)
        self.router.add_route(route)

    def check_intent(self, text: str) -> Dict[str, Any]:
        """
        Check if text matches any forbidden intents/topics.

        Args:
            text: Input text to check

        Returns:
            Dict with 'safe' boolean and 'reason' if unsafe
        """
        try:
            result = self.router.route(text)

            if result.matched:
                return {
                    "safe": False,
                    "reason": f"Triggered {result.name} guardrail",
                    "route": result.name,
                    "confidence": result.score,
                    "details": result.details,
                }

            return {"safe": True, "confidence": 1.0 - result.score}

        except ImportError:
            # Fallback if semantic dependencies not available
            logger.debug("Semantic router not available, returning safe")
            return {"safe": True, "fallback": True}

    def check_all_intents(self, text: str) -> List[Dict[str, Any]]:
        """
        Check text against all routes and return all matches.

        Args:
            text: Input text to check

        Returns:
            List of matching routes with details
        """
        try:
            matches = self.router.route_multi(text)
            return [
                {
                    "route": m.name,
                    "confidence": m.score,
                    "matched": m.matched,
                    "details": m.details,
                }
                for m in matches
            ]
        except ImportError:
            return []

    @property
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        try:
            return self.router.stats
        except:
            return {"initialized": False}
