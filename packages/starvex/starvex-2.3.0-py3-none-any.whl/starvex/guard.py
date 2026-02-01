"""
Starvex Guard - Pythonic SDK for AI Agent Protection

Provides an elegant, decorator-based API for protecting AI agents.

Example Usage:
    from starvex import StarvexGuard
    from starvex.rules import BlockPII, TopicRestriction

    # Initialize
    guard = StarvexGuard(
        rules=[
            BlockPII(),
            TopicRestriction(allowed_topics=["support", "billing"], sensitivity=0.8)
        ]
    )

    # Use as a Decorator (Easiest)
    @guard.protect
    def my_agent_chat(user_message):
        return agent_response

    # OR Use explicitly (More control)
    def chat_api(request):
        if not guard.check_input(request.text).passed:
            return "Sorry, I can't discuss that."

        response = agent.run(request.text)

        if not guard.check_output(response).passed:
            return "Error: Safety violation."

        return response
"""

import asyncio
import functools
import logging
import time
import uuid
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    Coroutine,
)
from dataclasses import dataclass, field

from .rules import GuardRule, RuleResult, RuleAction, default_rules

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CheckResult:
    """Result of a guard check"""

    passed: bool
    blocked_by: Optional[str] = None
    action: Optional[RuleAction] = None
    message: str = ""
    confidence: float = 1.0
    all_results: List[RuleResult] = field(default_factory=list)
    redacted_text: Optional[str] = None
    latency_ms: float = 0.0
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class GuardedResponse:
    """Response from a guarded function"""

    status: str  # "success", "blocked", "flagged"
    response: Optional[Any] = None
    input_check: Optional[CheckResult] = None
    output_check: Optional[CheckResult] = None
    error: Optional[str] = None
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    latency_ms: float = 0.0


class StarvexGuard:
    """
    Starvex Guard - Pythonic SDK for AI Agent Protection.

    A clean, decorator-based interface for protecting AI agents
    with composable guardrail rules.

    Example:
        ```python
        from starvex import StarvexGuard
        from starvex.rules import BlockPII, TopicRestriction

        guard = StarvexGuard(
            rules=[
                BlockPII(),
                TopicRestriction(allowed_topics=["support", "billing"])
            ]
        )

        @guard.protect
        def my_agent(message: str) -> str:
            return llm.generate(message)

        # Now my_agent is protected!
        result = my_agent("Hello, my SSN is 123-45-6789")
        # Returns error message instead of processing PII
        ```
    """

    def __init__(
        self,
        rules: Optional[List[GuardRule]] = None,
        api_key: Optional[str] = None,
        enable_tracing: bool = True,
        on_block: Optional[Callable[[CheckResult], str]] = None,
        on_flag: Optional[Callable[[CheckResult], None]] = None,
        log_level: str = "INFO",
    ):
        """
        Initialize StarvexGuard.

        Args:
            rules: List of GuardRule instances to apply
            api_key: Optional Starvex API key for cloud logging
            enable_tracing: Whether to log events to Starvex dashboard
            on_block: Custom handler when content is blocked
            on_flag: Custom handler when content is flagged
            log_level: Logging level
        """
        self.rules = rules if rules is not None else default_rules()
        self.api_key = api_key
        self.enable_tracing = enable_tracing
        self.on_block = on_block or self._default_block_handler
        self.on_flag = on_flag

        # Initialize tracer if API key provided
        self._tracer = None
        if api_key and enable_tracing:
            try:
                from ._internals.tracer import InternalTracer

                self._tracer = InternalTracer(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize tracer: {e}")

        # Configure logging
        logging.basicConfig(level=getattr(logging, log_level.upper()))

        logger.info(f"StarvexGuard initialized with {len(self.rules)} rules")

    def _default_block_handler(self, result: CheckResult) -> str:
        """Default message when content is blocked"""
        if result.blocked_by == "block_pii":
            return "I cannot process requests containing personal information."
        elif result.blocked_by == "block_jailbreak":
            return "I cannot process that request."
        elif result.blocked_by == "topic_restriction":
            return "I'm not able to discuss that topic."
        elif result.blocked_by == "block_toxicity":
            return "I cannot respond to inappropriate content."
        else:
            return "I cannot process that request due to safety policies."

    def check_input(self, text: str) -> CheckResult:
        """
        Check input text against all rules.

        Args:
            text: Input text to check

        Returns:
            CheckResult with pass/fail status and details
        """
        start_time = time.time()
        all_results: List[RuleResult] = []
        redacted_text = None

        for rule in self.rules:
            try:
                result = rule.check(text)
                all_results.append(result)

                # Handle redaction
                if result.action == RuleAction.REDACT and result.redacted_text:
                    redacted_text = result.redacted_text
                    text = redacted_text  # Use redacted text for subsequent checks

                # Check if blocked
                if not result.passed and result.action == RuleAction.BLOCK:
                    latency = (time.time() - start_time) * 1000
                    return CheckResult(
                        passed=False,
                        blocked_by=result.rule_name,
                        action=result.action,
                        message=result.message,
                        confidence=result.confidence,
                        all_results=all_results,
                        redacted_text=redacted_text,
                        latency_ms=latency,
                    )

            except Exception as e:
                logger.error(f"Error in rule {rule.name}: {e}")
                continue

        latency = (time.time() - start_time) * 1000
        return CheckResult(
            passed=True,
            all_results=all_results,
            redacted_text=redacted_text,
            latency_ms=latency,
            message="All checks passed",
        )

    def check_output(
        self,
        output_text: str,
        input_text: Optional[str] = None,
    ) -> CheckResult:
        """
        Check output text against all rules.

        Args:
            output_text: Agent output to check
            input_text: Original input (for context-aware checks)

        Returns:
            CheckResult with pass/fail status and details
        """
        start_time = time.time()
        all_results: List[RuleResult] = []
        redacted_text = None

        for rule in self.rules:
            try:
                if input_text:
                    result = rule.check_output(input_text, output_text)
                else:
                    result = rule.check(output_text)

                all_results.append(result)

                # Handle redaction
                if result.action == RuleAction.REDACT and result.redacted_text:
                    redacted_text = result.redacted_text

                # Check if blocked
                if not result.passed and result.action == RuleAction.BLOCK:
                    latency = (time.time() - start_time) * 1000
                    return CheckResult(
                        passed=False,
                        blocked_by=result.rule_name,
                        action=result.action,
                        message=result.message,
                        confidence=result.confidence,
                        all_results=all_results,
                        redacted_text=redacted_text,
                        latency_ms=latency,
                    )

            except Exception as e:
                logger.error(f"Error in rule {rule.name}: {e}")
                continue

        latency = (time.time() - start_time) * 1000
        return CheckResult(
            passed=True,
            all_results=all_results,
            redacted_text=redacted_text,
            latency_ms=latency,
            message="All checks passed",
        )

    def protect(
        self,
        func: Optional[Callable[..., T]] = None,
        *,
        check_input: bool = True,
        check_output: bool = True,
    ) -> Union[Callable[..., T], Callable[[Callable[..., T]], Callable[..., T]]]:
        """
        Decorator to protect a function with guardrails.

        Can be used with or without parentheses:

            @guard.protect
            def my_func(message):
                ...

            @guard.protect(check_output=False)
            def my_func(message):
                ...

        Args:
            func: Function to protect (when used without parens)
            check_input: Whether to check input
            check_output: Whether to check output

        Returns:
            Protected function or decorator
        """

        def decorator(fn: Callable[..., T]) -> Callable[..., T]:
            if asyncio.iscoroutinefunction(fn):

                @functools.wraps(fn)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    return await self._protected_call_async(
                        fn, args, kwargs, check_input, check_output
                    )

                return async_wrapper
            else:

                @functools.wraps(fn)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    return self._protected_call_sync(fn, args, kwargs, check_input, check_output)

                return sync_wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def _protected_call_sync(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        check_input: bool,
        check_output: bool,
    ) -> Any:
        """Execute protected sync function"""
        start_time = time.time()
        trace_id = str(uuid.uuid4())

        # Extract input text (first string argument)
        input_text = self._extract_input(args, kwargs)

        # Check input
        if check_input and input_text:
            input_result = self.check_input(input_text)

            if not input_result.passed:
                self._log_event(trace_id, input_text, None, "blocked", input_result)
                return self.on_block(input_result)

            # Use redacted text if available
            if input_result.redacted_text:
                args, kwargs = self._replace_input(args, kwargs, input_result.redacted_text)

        # Execute function
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Function execution error: {e}")
            raise

        # Check output
        if check_output and result:
            output_text = str(result) if not isinstance(result, str) else result
            output_result = self.check_output(output_text, input_text)

            if not output_result.passed:
                self._log_event(trace_id, input_text, output_text, "blocked", output_result)
                return self.on_block(output_result)

            # Use redacted output if available
            if output_result.redacted_text:
                result = output_result.redacted_text

        self._log_event(trace_id, input_text, str(result) if result else None, "success", None)
        return result

    async def _protected_call_async(
        self,
        func: Callable[..., Coroutine],
        args: tuple,
        kwargs: dict,
        check_input: bool,
        check_output: bool,
    ) -> Any:
        """Execute protected async function"""
        trace_id = str(uuid.uuid4())

        # Extract input text
        input_text = self._extract_input(args, kwargs)

        # Check input
        if check_input and input_text:
            input_result = self.check_input(input_text)

            if not input_result.passed:
                self._log_event(trace_id, input_text, None, "blocked", input_result)
                return self.on_block(input_result)

            if input_result.redacted_text:
                args, kwargs = self._replace_input(args, kwargs, input_result.redacted_text)

        # Execute function
        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Function execution error: {e}")
            raise

        # Check output
        if check_output and result:
            output_text = str(result) if not isinstance(result, str) else result
            output_result = self.check_output(output_text, input_text)

            if not output_result.passed:
                self._log_event(trace_id, input_text, output_text, "blocked", output_result)
                return self.on_block(output_result)

            if output_result.redacted_text:
                result = output_result.redacted_text

        self._log_event(trace_id, input_text, str(result) if result else None, "success", None)
        return result

    def _extract_input(self, args: tuple, kwargs: dict) -> Optional[str]:
        """Extract input text from function arguments"""
        # Try first positional arg
        if args and isinstance(args[0], str):
            return args[0]

        # Try common kwarg names
        for key in ["message", "text", "input", "prompt", "query", "content"]:
            if key in kwargs and isinstance(kwargs[key], str):
                return kwargs[key]

        return None

    def _replace_input(
        self,
        args: tuple,
        kwargs: dict,
        new_text: str,
    ) -> tuple:
        """Replace input text in function arguments"""
        if args and isinstance(args[0], str):
            return (new_text,) + args[1:], kwargs

        for key in ["message", "text", "input", "prompt", "query", "content"]:
            if key in kwargs and isinstance(kwargs[key], str):
                kwargs = {**kwargs, key: new_text}
                return args, kwargs

        return args, kwargs

    def _log_event(
        self,
        trace_id: str,
        input_text: Optional[str],
        output_text: Optional[str],
        status: str,
        result: Optional[CheckResult],
    ):
        """Log event to tracer if enabled"""
        if self._tracer:
            try:
                self._tracer.log_event(
                    trace_id=trace_id,
                    input_text=input_text or "",
                    output_text=output_text or "",
                    verdict=status,
                    confidence_score=result.confidence if result else 1.0,
                    latency_ms=result.latency_ms if result else 0,
                )
            except Exception as e:
                logger.debug(f"Failed to log event: {e}")

    def add_rule(self, rule: GuardRule) -> None:
        """Add a rule to the guard"""
        self.rules.append(rule)
        logger.info(f"Added rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name"""
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != rule_name]
        return len(self.rules) < original_count

    def get_rules(self) -> List[str]:
        """Get list of active rule names"""
        return [r.name for r in self.rules]

    # Context manager support
    def __enter__(self) -> "StarvexGuard":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._tracer:
            self._tracer.flush()

    async def __aenter__(self) -> "StarvexGuard":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._tracer:
            self._tracer.flush()


# Convenience alias
Guard = StarvexGuard
