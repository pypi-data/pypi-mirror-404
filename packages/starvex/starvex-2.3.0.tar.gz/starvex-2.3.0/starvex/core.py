"""
Starvex Core - Main SDK Interface
The primary interface for interacting with Starvex guardrails.
"""

import uuid
import time
import logging
import asyncio
import re
import threading
from typing import Optional, Callable, Any, Dict, List

from .models import (
    GuardVerdict,
    GuardConfig,
    GuardRule,
    GuardRuleType,
    GuardResponse,
    GuardCheckResult,
    DashboardConfig,
    SemanticRouteConfig,
)
from ._internals.tracer import InternalTracer
from ._internals.engine_nemo import NemoEngine
from ._internals.engine_eval import EvalEngine
from .utils import redact_sensitive_data, get_config_from_env, setup_logging, load_api_key

# Optional semantic router import
try:
    from ._internals.semantic_router import AccuracyEngine, Route

    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    AccuracyEngine = None
    Route = None

logger = logging.getLogger(__name__)


class Starvex:
    """
    Starvex - Production-ready AI agents with guardrails, observability, and security.

    Example Usage:
        ```python
        from starvex import Starvex

        vex = Starvex(api_key="sv_live_xxx")

        async def my_agent(prompt):
            return "Agent response"

        result = await vex.secure(prompt="Hello", agent_function=my_agent)
        ```

    Get your API key at: https://starvex.in/dashboard
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[GuardConfig] = None,
        redact_pii: bool = False,
        api_host: str = "https://decqadhkqnacujoyirkh.supabase.co/functions/v1",
        nemo_config_path: Optional[str] = None,
        enable_tracing: bool = True,
        log_level: str = "INFO",
        blocked_phrases: Optional[List[str]] = None,
        competitor_names: Optional[List[str]] = None,
        custom_jailbreak_patterns: Optional[List[str]] = None,
        custom_toxicity_patterns: Optional[List[str]] = None,
        auto_sync_config: bool = True,
        config_cache_ttl: int = 300,
        config_refresh_interval: Optional[int] = None,
        use_semantic_router: bool = False,
        semantic_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        semantic_device: str = "cpu",
        blocked_topics: Optional[List[str]] = None,
        custom_routes: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize Starvex SDK.

        Args:
            api_key: Your Starvex API key (sv_live_xxx or sv_test_xxx)
                     Get one at https://starvex.in/dashboard
            config: Optional GuardConfig for custom settings
            redact_pii: If True, PII will be masked before sending logs
            api_host: Starvex API host
            nemo_config_path: Path to NeMo Guardrails config directory
            enable_tracing: Enable/disable observability tracing
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            blocked_phrases: Custom phrases to block
            competitor_names: Competitor names to detect/block
            custom_jailbreak_patterns: Additional jailbreak regex patterns
            custom_toxicity_patterns: Additional toxicity regex patterns
            auto_sync_config: Automatically sync config from dashboard on init (default True)
            config_cache_ttl: How long to cache dashboard config in seconds (default 300 = 5 minutes)
            config_refresh_interval: Optional background refresh interval in seconds (None = disabled)
            use_semantic_router: Enable semantic routing for topic detection (requires sentence-transformers)
            semantic_model: HuggingFace sentence-transformers model for semantic routing
            semantic_device: Device for semantic model ("cpu" or "cuda")
            blocked_topics: List of default topic names to block: "politics", "competitors",
                           "investment_advice", "medical_advice", "legal_advice"
            custom_routes: List of custom route dicts with keys: name, utterances, sensitivity
        """
        setup_logging(log_level)

        # Load from environment or saved config if not provided
        env_config = get_config_from_env()
        self.api_key = api_key or env_config.get("api_key") or load_api_key()
        self.api_host = api_host or env_config.get("api_host")
        self.redact_pii = redact_pii or env_config.get("redact_pii", False)

        # Initialize configuration
        self.config = config or GuardConfig()

        # Initialize internal engines with custom patterns
        self.tracer = InternalTracer(
            api_key=self.api_key or "",
            host=self.api_host,
            enabled=enable_tracing and bool(self.api_key),
        )
        self.guard_engine = NemoEngine(
            config_path=nemo_config_path,
            blocked_phrases=blocked_phrases,
            competitor_patterns=[rf"\b{name}\b" for name in (competitor_names or [])],
            custom_jailbreak_patterns=custom_jailbreak_patterns,
            custom_toxicity_patterns=custom_toxicity_patterns,
        )
        self.eval_engine = EvalEngine()

        # Dashboard config (fetched from API or set locally)
        self._dashboard_config: Optional[DashboardConfig] = None
        self._config_cache_ttl = config_cache_ttl
        self._config_last_fetched: Optional[float] = None
        self._config_refresh_interval = config_refresh_interval
        self._refresh_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

        # Store custom config for reference
        self._blocked_phrases = blocked_phrases or []
        self._competitor_names = competitor_names or []

        # Initialize semantic router if enabled
        self._use_semantic_router = use_semantic_router
        self._accuracy_engine: Optional[Any] = None
        self._blocked_topics = set(blocked_topics or [])

        if use_semantic_router:
            if not SEMANTIC_AVAILABLE:
                logger.warning(
                    "Semantic router requested but sentence-transformers not installed. "
                    "Install with: pip install starvex[semantic]"
                )
            else:
                try:
                    self._accuracy_engine = AccuracyEngine(
                        model_name=semantic_model,
                        device=semantic_device,
                    )
                    # Add custom routes if provided
                    if custom_routes:
                        for route_config in custom_routes:
                            self._accuracy_engine.add_custom_route(
                                name=route_config["name"],
                                utterances=route_config["utterances"],
                                sensitivity=route_config.get("sensitivity", 0.75),
                            )
                    logger.info("Semantic router initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize semantic router: {e}")
                    self._use_semantic_router = False

        if self.api_key:
            logger.info("Starvex SDK initialized with API key")

            # Auto-sync config from dashboard if enabled
            if auto_sync_config:
                self._init_sync_config()

            # Start background refresh if interval is set
            if config_refresh_interval and config_refresh_interval > 0:
                self._start_config_refresh_thread()
        else:
            logger.warning(
                "Starvex SDK initialized without API key - run 'starvex login' or set STARVEX_API_KEY"
            )

    def _init_sync_config(self):
        """Synchronously sync config on init using a new event loop if needed."""
        try:
            # Try to get existing loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an async context, schedule it
                asyncio.create_task(self._async_sync_config_silent())
            except RuntimeError:
                # No running loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._async_sync_config_silent())
                finally:
                    loop.close()
        except Exception as e:
            logger.debug(f"Auto-sync config failed on init: {e}")

    async def _async_sync_config_silent(self):
        """Async helper for silent config sync."""
        try:
            await self.sync_config()
        except Exception as e:
            logger.debug(f"Failed to sync config: {e}")

    def _start_config_refresh_thread(self):
        """Start background thread to periodically refresh config."""

        def refresh_loop():
            while not self._shutdown_event.is_set():
                self._shutdown_event.wait(self._config_refresh_interval or 300)
                if self._shutdown_event.is_set():
                    break
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.sync_config())
                        logger.debug("Background config refresh completed")
                    finally:
                        loop.close()
                except Exception as e:
                    logger.debug(f"Background config refresh failed: {e}")

        self._refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self._refresh_thread.start()
        logger.debug(f"Started config refresh thread (interval: {self._config_refresh_interval}s)")

    def is_config_cached(self) -> bool:
        """Check if config is cached and still valid."""
        if self._dashboard_config is None or self._config_last_fetched is None:
            return False
        elapsed = time.time() - self._config_last_fetched
        return elapsed < self._config_cache_ttl

    async def secure(
        self,
        prompt: str,
        agent_function: Callable[[str], Any],
        context: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        skip_input_check: bool = False,
        skip_output_check: bool = False,
    ) -> GuardResponse:
        """
        The Master Function - Secures an AI agent interaction.

        1. Checks Input Safety (jailbreak, PII, toxicity)
        2. Calls the Agent Function
        3. Checks Output Quality (hallucination, toxicity)
        4. Logs everything to observability platform

        Args:
            prompt: User input prompt
            agent_function: Async or sync function that takes prompt and returns response
            context: Optional context for hallucination checking
            user_id: Optional user identifier for tracing
            session_id: Optional session identifier for tracing
            metadata: Optional additional metadata
            skip_input_check: Skip pre-flight input safety check
            skip_output_check: Skip post-flight output quality check

        Returns:
            GuardResponse with status, response, and detailed checks
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        all_checks: List[GuardCheckResult] = []

        # Prepare logging text (potentially redacted)
        log_prompt = redact_sensitive_data(prompt) if self.redact_pii else prompt

        # --- STEP 1: PRE-FLIGHT CHECK ---
        if not skip_input_check:
            is_safe, block_msg, input_checks = await self.guard_engine.check_input(
                prompt,
                check_jailbreak=True,
                check_pii=self._should_block_pii(),
                check_toxicity=True,
            )
            all_checks.extend(input_checks)

            if not is_safe:
                verdict = self._get_verdict_from_checks(input_checks)
                latency_ms = (time.time() - start_time) * 1000

                self.tracer.log_event(
                    trace_id=trace_id,
                    input_text=log_prompt,
                    output_text=block_msg,
                    verdict=verdict,
                    confidence_score=1.0,
                    user_id=user_id,
                    session_id=session_id,
                    latency_ms=latency_ms,
                    checks=all_checks,
                    metadata=metadata,
                )

                return GuardResponse(
                    status="blocked",
                    response=block_msg,
                    verdict=verdict,
                    checks=all_checks,
                    trace_id=trace_id,
                    latency_ms=latency_ms,
                )

            # --- STEP 1b: SEMANTIC TOPIC CHECK ---
            if self._use_semantic_router and self._accuracy_engine:
                topic_result = self._accuracy_engine.check_intent(prompt)

                if not topic_result.get("safe", True):
                    route_name = topic_result.get("route", "unknown")

                    # Check if this topic should be blocked
                    should_block = (
                        not self._blocked_topics  # Block all if no specific list
                        or route_name in self._blocked_topics
                    )

                    topic_check = GuardCheckResult(
                        rule_type=GuardRuleType.TOPIC,
                        passed=not should_block,
                        confidence=topic_result.get("confidence", 0.0),
                        message=f"Matched topic: {route_name}",
                        details=topic_result.get("details"),
                    )
                    all_checks.append(topic_check)

                    if should_block:
                        block_msg = f"This request was blocked because it relates to a restricted topic: {route_name}"
                        latency_ms = (time.time() - start_time) * 1000

                        self.tracer.log_event(
                            trace_id=trace_id,
                            input_text=log_prompt,
                            output_text=block_msg,
                            verdict=GuardVerdict.BLOCKED_TOPIC,
                            confidence_score=topic_result.get("confidence", 0.0),
                            user_id=user_id,
                            session_id=session_id,
                            latency_ms=latency_ms,
                            checks=all_checks,
                            metadata=metadata,
                        )

                        return GuardResponse(
                            status="blocked",
                            response=block_msg,
                            verdict=GuardVerdict.BLOCKED_TOPIC,
                            checks=all_checks,
                            trace_id=trace_id,
                            latency_ms=latency_ms,
                        )
                else:
                    # Log that topic check passed
                    topic_check = GuardCheckResult(
                        rule_type=GuardRuleType.TOPIC,
                        passed=True,
                        confidence=topic_result.get("confidence", 1.0),
                        message="No restricted topics detected",
                    )
                    all_checks.append(topic_check)

        # --- STEP 2: AGENT EXECUTION ---
        try:
            if asyncio.iscoroutinefunction(agent_function):
                agent_response = await agent_function(prompt)
            else:
                agent_response = agent_function(prompt)

            if not isinstance(agent_response, str):
                agent_response = str(agent_response)

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            self.tracer.log_event(
                trace_id=trace_id,
                input_text=log_prompt,
                output_text=str(e),
                verdict=GuardVerdict.FAILED_SYSTEM,
                confidence_score=0.0,
                user_id=user_id,
                session_id=session_id,
                latency_ms=latency_ms,
                checks=all_checks,
                metadata={"error": str(e), **(metadata or {})},
            )

            raise

        log_response = redact_sensitive_data(agent_response) if self.redact_pii else agent_response

        # --- STEP 3: POST-FLIGHT CHECK ---
        warning = None
        final_verdict = GuardVerdict.PASSED

        if not skip_output_check:
            is_safe, block_msg, output_checks = await self.guard_engine.check_output(
                prompt, agent_response, check_pii=self._should_block_pii(), check_toxicity=True
            )
            all_checks.extend(output_checks)

            if not is_safe:
                final_verdict = self._get_verdict_from_checks(output_checks)
                latency_ms = (time.time() - start_time) * 1000

                self.tracer.log_event(
                    trace_id=trace_id,
                    input_text=log_prompt,
                    output_text=log_response,
                    verdict=final_verdict,
                    confidence_score=1.0,
                    user_id=user_id,
                    session_id=session_id,
                    latency_ms=latency_ms,
                    checks=all_checks,
                    metadata=metadata,
                )

                return GuardResponse(
                    status="blocked",
                    response=block_msg,
                    verdict=final_verdict,
                    checks=all_checks,
                    trace_id=trace_id,
                    latency_ms=latency_ms,
                )

            # Hallucination check
            hallucination_result = self.eval_engine.evaluate_with_result(
                prompt, agent_response, context
            )
            all_checks.append(hallucination_result)

            if not hallucination_result.passed:
                final_verdict = GuardVerdict.FAILED_HALLUCINATION
                warning = f"High hallucination risk (score: {hallucination_result.confidence:.2f})"

        # --- STEP 4: SUCCESS ---
        latency_ms = (time.time() - start_time) * 1000
        status = "flagged" if warning else "success"

        confidence = 0.0
        if final_verdict != GuardVerdict.PASSED:
            for check in all_checks:
                if check.rule_type == GuardRuleType.HALLUCINATION and not check.passed:
                    confidence = check.confidence
                    break

        self.tracer.log_event(
            trace_id=trace_id,
            input_text=log_prompt,
            output_text=log_response,
            verdict=final_verdict,
            confidence_score=confidence,
            user_id=user_id,
            session_id=session_id,
            latency_ms=latency_ms,
            checks=all_checks,
            metadata=metadata,
        )

        return GuardResponse(
            status=status,
            response=agent_response,
            verdict=final_verdict,
            checks=all_checks,
            trace_id=trace_id,
            latency_ms=latency_ms,
            warning=warning,
        )

    async def protect(
        self, prompt: str, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> GuardResponse:
        """
        Check input only (no agent execution).
        Use this for pre-screening prompts before sending to any LLM.

        Args:
            prompt: User input to check
            user_id: Optional user identifier
            session_id: Optional session identifier

        Returns:
            GuardResponse with check results
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()

        log_prompt = redact_sensitive_data(prompt) if self.redact_pii else prompt

        is_safe, block_msg, checks = await self.guard_engine.check_input(prompt)

        # Also run semantic topic check if enabled
        if is_safe and self._use_semantic_router and self._accuracy_engine:
            topic_result = self._accuracy_engine.check_intent(prompt)

            if not topic_result.get("safe", True):
                route_name = topic_result.get("route", "unknown")
                should_block = not self._blocked_topics or route_name in self._blocked_topics

                topic_check = GuardCheckResult(
                    rule_type=GuardRuleType.TOPIC,
                    passed=not should_block,
                    confidence=topic_result.get("confidence", 0.0),
                    message=f"Matched topic: {route_name}",
                    details=topic_result.get("details"),
                )
                checks.append(topic_check)

                if should_block:
                    is_safe = False
                    block_msg = f"This request was blocked because it relates to a restricted topic: {route_name}"
            else:
                topic_check = GuardCheckResult(
                    rule_type=GuardRuleType.TOPIC,
                    passed=True,
                    confidence=topic_result.get("confidence", 1.0),
                    message="No restricted topics detected",
                )
                checks.append(topic_check)

        latency_ms = (time.time() - start_time) * 1000
        verdict = GuardVerdict.PASSED if is_safe else self._get_verdict_from_checks(checks)

        self.tracer.log_event(
            trace_id=trace_id,
            input_text=log_prompt,
            output_text=block_msg,
            verdict=verdict,
            confidence_score=0.0 if is_safe else 1.0,
            user_id=user_id,
            session_id=session_id,
            latency_ms=latency_ms,
            checks=checks,
        )

        return GuardResponse(
            status="success" if is_safe else "blocked",
            response=block_msg,
            verdict=verdict,
            checks=checks,
            trace_id=trace_id,
            latency_ms=latency_ms,
        )

    def test(
        self, prompt: str, response: str, context: Optional[List[str]] = None
    ) -> GuardResponse:
        """
        Test mode - evaluate a prompt/response pair without tracing.
        Use this for testing and development.

        Args:
            prompt: Test prompt
            response: Test response
            context: Optional context for evaluation

        Returns:
            GuardResponse with evaluation results
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        checks: List[GuardCheckResult] = []

        metrics = self.eval_engine.full_evaluation(prompt, response, context)

        checks.append(
            GuardCheckResult(
                rule_type=GuardRuleType.HALLUCINATION,
                passed=metrics.hallucination_score < 0.5,
                confidence=metrics.hallucination_score,
                message=f"Hallucination score: {metrics.hallucination_score:.2f}",
            )
        )

        checks.append(
            GuardCheckResult(
                rule_type=GuardRuleType.TOXICITY,
                passed=metrics.toxicity_score < 0.3,
                confidence=metrics.toxicity_score,
                message=f"Toxicity score: {metrics.toxicity_score:.2f}",
            )
        )

        latency_ms = (time.time() - start_time) * 1000

        all_passed = all(c.passed for c in checks)
        verdict = GuardVerdict.PASSED if all_passed else self._get_verdict_from_checks(checks)

        return GuardResponse(
            status="success" if all_passed else "flagged",
            response=response,
            verdict=verdict,
            checks=checks,
            trace_id=trace_id,
            latency_ms=latency_ms,
            metadata={"metrics": metrics.model_dump()},
        )

    def add_rule(self, rule: GuardRule):
        """Add a guard rule to the configuration"""
        self.config.rules.append(rule)
        logger.info(f"Added rule: {rule.rule_type.value}")

    def remove_rule(self, rule_type: GuardRuleType):
        """Remove all rules of a specific type"""
        self.config.rules = [r for r in self.config.rules if r.rule_type != rule_type]
        logger.info(f"Removed rules of type: {rule_type.value}")

    def add_topic_route(
        self,
        name: str,
        utterances: List[str],
        sensitivity: float = 0.75,
        block: bool = True,
    ) -> bool:
        """
        Add a custom topic route for semantic detection.

        Args:
            name: Name of the topic/route (e.g., "healthcare", "finance")
            utterances: Example phrases that should match this topic
            sensitivity: Threshold for matching (0-1, higher = stricter)
            block: If True, add this topic to the blocked list

        Returns:
            True if route was added successfully, False otherwise
        """
        if not self._use_semantic_router or not self._accuracy_engine:
            logger.warning("Semantic router not enabled. Enable with use_semantic_router=True")
            return False

        try:
            self._accuracy_engine.add_custom_route(
                name=name,
                utterances=utterances,
                sensitivity=sensitivity,
            )
            if block:
                self._blocked_topics.add(name)
            logger.info(f"Added topic route: {name}")
            return True
        except Exception as e:
            logger.warning(f"Failed to add topic route: {e}")
            return False

    def remove_topic_route(self, name: str) -> bool:
        """
        Remove a topic route from semantic detection.

        Args:
            name: Name of the topic/route to remove

        Returns:
            True if route was removed successfully, False otherwise
        """
        if not self._use_semantic_router or not self._accuracy_engine:
            return False

        try:
            result = self._accuracy_engine.router.remove_route(name)
            self._blocked_topics.discard(name)
            return result
        except Exception:
            return False

    def list_topic_routes(self) -> List[str]:
        """Get list of all registered topic routes"""
        if not self._use_semantic_router or not self._accuracy_engine:
            return []
        return self._accuracy_engine.router.routes

    def get_semantic_stats(self) -> Dict[str, Any]:
        """Get semantic router statistics"""
        if not self._use_semantic_router or not self._accuracy_engine:
            return {"enabled": False}
        stats = self._accuracy_engine.stats
        stats["blocked_topics"] = list(self._blocked_topics)
        return stats

    async def sync_config(self, force: bool = False) -> DashboardConfig:
        """
        Sync configuration from Starvex Dashboard.
        Call this on startup to get latest rules from dashboard.

        Args:
            force: If True, bypass cache and fetch fresh config

        Returns:
            DashboardConfig with current settings
        """
        if not self.api_key:
            logger.warning("Cannot sync config without API key")
            return DashboardConfig()

        # Check cache unless force refresh
        if not force and self.is_config_cached():
            logger.debug("Using cached dashboard config")
            return self._dashboard_config  # type: ignore

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_host}/get-settings",
                    headers={"x-api-key": self.api_key},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    self._dashboard_config = DashboardConfig(**data)
                    self._config_last_fetched = time.time()

                    # Update guard engine with dashboard config
                    if self._dashboard_config.custom_blocked_phrases:
                        self.guard_engine._blocked_phrases = set(
                            p.lower() for p in self._dashboard_config.custom_blocked_phrases
                        )
                    if self._dashboard_config.competitor_names:
                        patterns = [
                            rf"\b{name}\b" for name in self._dashboard_config.competitor_names
                        ]
                        self.guard_engine._competitor_patterns = patterns
                        self.guard_engine._compiled_competitor = [
                            re.compile(p, re.IGNORECASE) for p in patterns
                        ]

                    # Sync semantic routes from dashboard
                    self._sync_semantic_routes()

                    logger.info("Dashboard configuration synced")
                    return self._dashboard_config
        except Exception as e:
            logger.warning(f"Failed to sync config: {e}")

        if not self._dashboard_config:
            self._dashboard_config = DashboardConfig()
        return self._dashboard_config

    def _sync_semantic_routes(self):
        """Sync semantic routes from dashboard config to the accuracy engine."""
        if not self._dashboard_config:
            return

        if not self._dashboard_config.semantic_routes:
            return

        # Initialize semantic router if not already done and routes exist
        if not self._use_semantic_router and self._dashboard_config.semantic_routes:
            if SEMANTIC_AVAILABLE:
                try:
                    from ._internals.semantic_router import AccuracyEngine

                    self._accuracy_engine = AccuracyEngine(
                        model_name="sentence-transformers/all-MiniLM-L6-v2",
                        device="cpu",
                    )
                    self._use_semantic_router = True
                    logger.info("Semantic router auto-initialized from dashboard config")
                except Exception as e:
                    logger.warning(f"Failed to initialize semantic router: {e}")
                    return
            else:
                logger.debug("Semantic routes found but sentence-transformers not installed")
                return

        if not self._accuracy_engine:
            return

        # Clear existing routes and add from dashboard
        for route_name in list(self._accuracy_engine.router.routes):
            self._accuracy_engine.router.remove_route(route_name)

        self._blocked_topics.clear()

        for route_config in self._dashboard_config.semantic_routes:
            if not route_config.enabled:
                continue

            if not route_config.utterances:
                continue

            try:
                self._accuracy_engine.add_custom_route(
                    name=route_config.name,
                    utterances=route_config.utterances,
                    sensitivity=route_config.sensitivity,
                )

                # Add to blocked topics if action is "block"
                if route_config.action == "block":
                    self._blocked_topics.add(route_config.name)

                logger.debug(
                    f"Synced semantic route: {route_config.name} (action: {route_config.action})"
                )

            except Exception as e:
                logger.warning(f"Failed to add semantic route '{route_config.name}': {e}")

        logger.info(
            f"Synced {len(self._dashboard_config.semantic_routes)} semantic routes from dashboard"
        )

    def set_dashboard_config(self, config: DashboardConfig):
        """Set dashboard configuration locally"""
        self._dashboard_config = config
        logger.info("Dashboard configuration updated")

    def _should_block_pii(self) -> bool:
        """Check if PII should be blocked based on config"""
        if self._dashboard_config:
            return self._dashboard_config.block_pii

        for rule in self.config.rules:
            if rule.rule_type == GuardRuleType.PII and rule.enabled:
                return True

        return True  # Default to blocking PII

    def _get_verdict_from_checks(self, checks: List[GuardCheckResult]) -> GuardVerdict:
        """Determine verdict from check results"""
        for check in checks:
            if not check.passed:
                if check.rule_type == GuardRuleType.JAILBREAK:
                    return GuardVerdict.BLOCKED_JAILBREAK
                elif check.rule_type == GuardRuleType.PII:
                    return GuardVerdict.BLOCKED_PII
                elif check.rule_type == GuardRuleType.TOXICITY:
                    return GuardVerdict.BLOCKED_TOXICITY
                elif check.rule_type == GuardRuleType.COMPETITOR:
                    return GuardVerdict.BLOCKED_COMPETITOR
                elif check.rule_type == GuardRuleType.CUSTOM:
                    return GuardVerdict.BLOCKED_CUSTOM
                elif check.rule_type == GuardRuleType.TOPIC:
                    return GuardVerdict.BLOCKED_TOPIC
                elif check.rule_type == GuardRuleType.HALLUCINATION:
                    return GuardVerdict.FAILED_HALLUCINATION

        return GuardVerdict.PASSED

    def flush(self):
        """Flush pending events to the server"""
        self.tracer.flush()

    def shutdown(self):
        """Shutdown the SDK gracefully"""
        # Stop background refresh thread
        if self._refresh_thread and self._refresh_thread.is_alive():
            self._shutdown_event.set()
            self._refresh_thread.join(timeout=2)
            logger.debug("Config refresh thread stopped")

        self.tracer.shutdown()
        logger.info("Starvex SDK shutdown complete")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
