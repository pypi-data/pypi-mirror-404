"""
Starvex - Production-ready AI agents with semantic guardrails, observability, and security

Build AI agents that are safe, measurable, and ready to ship.

Quick Start (New Pythonic API):
    ```python
    from starvex import StarvexGuard
    from starvex.rules import BlockPII, TopicRestriction

    # Initialize with rules
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

    # OR use explicitly (More control)
    def chat_api(request):
        if not guard.check_input(request.text).passed:
            return "Sorry, I can't discuss that."

        response = agent.run(request.text)

        if not guard.check_output(response).passed:
            return "Error: Safety violation."

        return response
    ```

Legacy API (still supported):
    ```python
    from starvex import Starvex

    vex = Starvex(api_key="sv_live_xxx")

    async def my_agent(prompt: str) -> str:
        return "Agent response"

    result = await vex.secure(
        prompt="User input",
        agent_function=my_agent
    )
    ```

Get your API key at: https://starvex.in/dashboard
Documentation: https://starvex.in/docs
"""

# Core classes
from .core import Starvex
from .guard import StarvexGuard, Guard, CheckResult, GuardedResponse

# Models
from .models import (
    GuardVerdict,
    GuardRule as GuardRuleModel,
    GuardRuleType,
    GuardConfig,
    GuardInput,
    GuardResponse,
    GuardCheckResult,
    EvalMetrics,
    DashboardConfig,
)

# Rules (New API)
from .rules import (
    GuardRule,
    RuleResult,
    RuleAction,
    BlockPII,
    TopicRestriction,
    BlockJailbreak,
    BlockToxicity,
    BlockCompetitor,
    PolicyCompliance,
    CustomBlocklist,
    default_rules,
    strict_rules,
    enterprise_rules,
)

# Utilities
from .utils import (
    generate_api_key,
    validate_api_key_format,
    redact_sensitive_data,
    setup_logging,
)

# Instrumentation
from .instrument import instrument, get_stats, get_calls

# Hybrid Accuracy Architecture (Advanced)
from ._internals.hybrid_router import (
    HybridRouter,
    HybridRouteResult,
    create_hybrid_router,
)
from ._internals.auto_fix_pipeline import (
    AutoFixPipeline,
    run_auto_fix,
)

__version__ = "2.3.0"
__author__ = "Starvex Team"
__all__ = [
    # New API (Recommended)
    "StarvexGuard",
    "Guard",
    "CheckResult",
    "GuardedResponse",
    # Rules
    "GuardRule",
    "RuleResult",
    "RuleAction",
    "BlockPII",
    "TopicRestriction",
    "BlockJailbreak",
    "BlockToxicity",
    "BlockCompetitor",
    "PolicyCompliance",
    "CustomBlocklist",
    "default_rules",
    "strict_rules",
    "enterprise_rules",
    # Legacy API
    "Starvex",
    # Models
    "GuardVerdict",
    "GuardRuleModel",
    "GuardRuleType",
    "GuardConfig",
    "GuardInput",
    "GuardResponse",
    "GuardCheckResult",
    "EvalMetrics",
    "DashboardConfig",
    # Utilities
    "generate_api_key",
    "validate_api_key_format",
    "redact_sensitive_data",
    "setup_logging",
    # Instrumentation
    "instrument",
    "get_stats",
    "get_calls",
    # Hybrid Accuracy Architecture
    "HybridRouter",
    "HybridRouteResult",
    "create_hybrid_router",
    "AutoFixPipeline",
    "run_auto_fix",
]
