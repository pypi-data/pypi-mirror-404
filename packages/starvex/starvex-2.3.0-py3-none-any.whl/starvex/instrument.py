"""
Starvex Instrument - Automatic observability for AI libraries.

One-line instrumentation for popular AI libraries.

Example:
    import starvex
    import openai

    # One line to track everything
    starvex.instrument(openai)

    # Now every OpenAI call is automatically logged with:
    # - Latency
    # - Token count
    # - Guardrail status
    # - Cost estimation
"""

import functools
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class InstrumentedCall:
    """Record of an instrumented API call"""

    def __init__(
        self,
        provider: str,
        method: str,
        start_time: float,
    ):
        self.id = str(uuid.uuid4())
        self.provider = provider
        self.method = method
        self.start_time = start_time
        self.end_time: Optional[float] = None
        self.latency_ms: float = 0.0
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.total_tokens: int = 0
        self.model: Optional[str] = None
        self.status: str = "pending"
        self.error: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def complete(self, response: Any = None, error: str = None):
        """Mark call as complete"""
        self.end_time = time.time()
        self.latency_ms = (self.end_time - self.start_time) * 1000

        if error:
            self.status = "error"
            self.error = error
        else:
            self.status = "success"

            # Extract token info from response
            if response:
                self._extract_usage(response)

    def _extract_usage(self, response: Any):
        """Extract usage information from response"""
        # OpenAI format
        if hasattr(response, "usage"):
            usage = response.usage
            if hasattr(usage, "prompt_tokens"):
                self.input_tokens = usage.prompt_tokens
            if hasattr(usage, "completion_tokens"):
                self.output_tokens = usage.completion_tokens
            if hasattr(usage, "total_tokens"):
                self.total_tokens = usage.total_tokens

        # Dict format
        elif isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            self.input_tokens = usage.get("prompt_tokens", 0)
            self.output_tokens = usage.get("completion_tokens", 0)
            self.total_tokens = usage.get("total_tokens", 0)

        # Extract model
        if hasattr(response, "model"):
            self.model = response.model
        elif isinstance(response, dict) and "model" in response:
            self.model = response["model"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "provider": self.provider,
            "method": self.method,
            "latency_ms": self.latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
        }


class Instrumentor:
    """
    Auto-instruments AI libraries for observability.

    Supports:
    - OpenAI
    - Anthropic
    - LangChain
    - And more...
    """

    _instance = None
    _calls: List[InstrumentedCall] = []
    _callbacks: List[Callable[[InstrumentedCall], None]] = []
    _guard = None
    _api_key: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def instrument(
        cls,
        library: Any,
        guard=None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Instrument a library for automatic tracking.

        Args:
            library: The library module to instrument (e.g., openai)
            guard: Optional StarvexGuard for input/output checking
            api_key: Optional Starvex API key for cloud logging
        """
        instance = cls()
        instance._guard = guard
        instance._api_key = api_key

        library_name = library.__name__

        if library_name == "openai":
            instance._instrument_openai(library)
        elif library_name == "anthropic":
            instance._instrument_anthropic(library)
        elif library_name == "langchain":
            instance._instrument_langchain(library)
        else:
            logger.warning(f"Unknown library: {library_name}. Attempting generic instrumentation.")
            instance._instrument_generic(library)

        logger.info(f"Instrumented {library_name}")

    def _instrument_openai(self, openai_module: Any) -> None:
        """Instrument OpenAI library"""
        try:
            # OpenAI v1 API
            if hasattr(openai_module, "OpenAI"):
                original_init = openai_module.OpenAI.__init__

                @functools.wraps(original_init)
                def patched_init(self, *args, **kwargs):
                    original_init(self, *args, **kwargs)
                    # Patch chat completions
                    if hasattr(self, "chat") and hasattr(self.chat, "completions"):
                        original_create = self.chat.completions.create
                        self.chat.completions.create = self._wrap_method(
                            original_create, "openai", "chat.completions.create"
                        )

                openai_module.OpenAI.__init__ = patched_init

            # Also instrument the module-level client if exists
            if hasattr(openai_module, "chat"):
                original_create = openai_module.chat.completions.create
                openai_module.chat.completions.create = self._wrap_method(
                    original_create, "openai", "chat.completions.create"
                )

        except Exception as e:
            logger.error(f"Failed to instrument OpenAI: {e}")

    def _instrument_anthropic(self, anthropic_module: Any) -> None:
        """Instrument Anthropic library"""
        try:
            if hasattr(anthropic_module, "Anthropic"):
                original_init = anthropic_module.Anthropic.__init__

                @functools.wraps(original_init)
                def patched_init(self, *args, **kwargs):
                    original_init(self, *args, **kwargs)
                    if hasattr(self, "messages"):
                        original_create = self.messages.create
                        self.messages.create = self._wrap_method(
                            original_create, "anthropic", "messages.create"
                        )

                anthropic_module.Anthropic.__init__ = patched_init

        except Exception as e:
            logger.error(f"Failed to instrument Anthropic: {e}")

    def _instrument_langchain(self, langchain_module: Any) -> None:
        """Instrument LangChain"""
        try:
            # Instrument LLM base class
            if hasattr(langchain_module, "llms"):
                base_llm = langchain_module.llms.base.BaseLLM
                original_call = base_llm.__call__
                base_llm.__call__ = self._wrap_method(original_call, "langchain", "llm.call")

        except Exception as e:
            logger.error(f"Failed to instrument LangChain: {e}")

    def _instrument_generic(self, module: Any) -> None:
        """Generic instrumentation attempt"""
        # Try to find and wrap common method patterns
        methods_to_wrap = ["generate", "create", "complete", "chat", "invoke", "run"]

        for attr_name in dir(module):
            attr = getattr(module, attr_name, None)
            if callable(attr) and attr_name in methods_to_wrap:
                wrapped = self._wrap_method(attr, module.__name__, attr_name)
                setattr(module, attr_name, wrapped)

    def _wrap_method(
        self,
        method: Callable,
        provider: str,
        method_name: str,
    ) -> Callable:
        """Wrap a method with instrumentation"""
        instrumentor = self

        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            call = InstrumentedCall(
                provider=provider,
                method=method_name,
                start_time=time.time(),
            )

            try:
                # Check input if guard is set
                if instrumentor._guard:
                    input_text = instrumentor._extract_input_from_args(args, kwargs)
                    if input_text:
                        check_result = instrumentor._guard.check_input(input_text)
                        if not check_result.passed:
                            call.complete(error="Input blocked by guardrail")
                            call.metadata["blocked_by"] = check_result.blocked_by
                            instrumentor._record_call(call)
                            raise ValueError(f"Input blocked: {check_result.message}")

                # Execute original method
                result = method(*args, **kwargs)

                # Check output if guard is set
                if instrumentor._guard:
                    output_text = instrumentor._extract_output_from_result(result)
                    if output_text:
                        check_result = instrumentor._guard.check_output(output_text)
                        if not check_result.passed:
                            call.complete(error="Output blocked by guardrail")
                            call.metadata["blocked_by"] = check_result.blocked_by
                            instrumentor._record_call(call)
                            raise ValueError(f"Output blocked: {check_result.message}")

                call.complete(response=result)
                instrumentor._record_call(call)

                return result

            except Exception as e:
                if call.status == "pending":
                    call.complete(error=str(e))
                    instrumentor._record_call(call)
                raise

        @functools.wraps(method)
        async def async_wrapper(*args, **kwargs):
            call = InstrumentedCall(
                provider=provider,
                method=method_name,
                start_time=time.time(),
            )

            try:
                result = await method(*args, **kwargs)
                call.complete(response=result)
                instrumentor._record_call(call)
                return result
            except Exception as e:
                call.complete(error=str(e))
                instrumentor._record_call(call)
                raise

        import asyncio

        if asyncio.iscoroutinefunction(method):
            return async_wrapper
        return wrapper

    def _extract_input_from_args(self, args: tuple, kwargs: dict) -> Optional[str]:
        """Extract input text from method arguments"""
        # OpenAI format
        if "messages" in kwargs:
            messages = kwargs["messages"]
            if messages and isinstance(messages, list):
                last_user = next((m for m in reversed(messages) if m.get("role") == "user"), None)
                if last_user:
                    return last_user.get("content", "")

        # Prompt format
        if "prompt" in kwargs:
            return kwargs["prompt"]

        # First string arg
        for arg in args:
            if isinstance(arg, str):
                return arg

        return None

    def _extract_output_from_result(self, result: Any) -> Optional[str]:
        """Extract output text from result"""
        # OpenAI format
        if hasattr(result, "choices") and result.choices:
            choice = result.choices[0]
            if hasattr(choice, "message"):
                return choice.message.content
            if hasattr(choice, "text"):
                return choice.text

        # Dict format
        if isinstance(result, dict):
            if "choices" in result and result["choices"]:
                choice = result["choices"][0]
                if "message" in choice:
                    return choice["message"].get("content", "")
                if "text" in choice:
                    return choice["text"]

        # String result
        if isinstance(result, str):
            return result

        return None

    def _record_call(self, call: InstrumentedCall) -> None:
        """Record a completed call"""
        self._calls.append(call)

        # Keep only last 1000 calls in memory
        if len(self._calls) > 1000:
            self._calls = self._calls[-1000:]

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(call)
            except Exception as e:
                logger.debug(f"Callback error: {e}")

        # Log to console
        logger.debug(
            f"[{call.provider}] {call.method} - "
            f"{call.latency_ms:.2f}ms - "
            f"{call.total_tokens} tokens - "
            f"{call.status}"
        )

    @classmethod
    def add_callback(cls, callback: Callable[[InstrumentedCall], None]) -> None:
        """Add a callback for instrumented calls"""
        cls._callbacks.append(callback)

    @classmethod
    def get_calls(cls) -> List[InstrumentedCall]:
        """Get all recorded calls"""
        return cls._calls.copy()

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get aggregated statistics"""
        if not cls._calls:
            return {"total_calls": 0}

        total_latency = sum(c.latency_ms for c in cls._calls)
        total_tokens = sum(c.total_tokens for c in cls._calls)
        error_count = sum(1 for c in cls._calls if c.status == "error")

        return {
            "total_calls": len(cls._calls),
            "avg_latency_ms": total_latency / len(cls._calls),
            "total_tokens": total_tokens,
            "error_rate": error_count / len(cls._calls),
            "by_provider": cls._stats_by_provider(),
        }

    @classmethod
    def _stats_by_provider(cls) -> Dict[str, Dict[str, Any]]:
        """Get stats grouped by provider"""
        providers: Dict[str, List[InstrumentedCall]] = {}

        for call in cls._calls:
            if call.provider not in providers:
                providers[call.provider] = []
            providers[call.provider].append(call)

        return {
            provider: {
                "calls": len(calls),
                "avg_latency_ms": sum(c.latency_ms for c in calls) / len(calls),
                "total_tokens": sum(c.total_tokens for c in calls),
            }
            for provider, calls in providers.items()
        }

    @classmethod
    def clear(cls) -> None:
        """Clear all recorded calls"""
        cls._calls.clear()


# Module-level function for easy access
def instrument(library: Any, guard=None, api_key: Optional[str] = None) -> None:
    """
    Instrument a library for automatic observability.

    Example:
        import starvex
        import openai

        starvex.instrument(openai)
    """
    Instrumentor.instrument(library, guard=guard, api_key=api_key)


def get_stats() -> Dict[str, Any]:
    """Get instrumentation statistics"""
    return Instrumentor.get_stats()


def get_calls() -> List[InstrumentedCall]:
    """Get recorded API calls"""
    return Instrumentor.get_calls()
