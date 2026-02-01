# Starvex

Production-ready AI agents with semantic guardrails, observability, and security.

## Installation

```bash
pip install starvex
```

For full features including semantic understanding and PII detection:

```bash
pip install starvex[full]
```

Or install specific features:

```bash
pip install starvex[pii]        # PII detection with Presidio
pip install starvex[semantic]   # Semantic topic routing
pip install starvex[nli]        # Natural language inference
pip install starvex[vector]     # Pinecone vector search
```

## Quick Start (v2.0 - New Pythonic API)

### 1. Get your API key at [starvex.in/dashboard](https://starvex.in/dashboard)

### 2. Use the Decorator API (Recommended)

```python
from starvex import StarvexGuard
from starvex.rules import BlockPII, TopicRestriction, BlockJailbreak

# Initialize with composable rules
guard = StarvexGuard(
    api_key="sv_live_xxx",  # Optional: enables dashboard logging
    rules=[
        BlockPII(),
        BlockJailbreak(),
        TopicRestriction(
            blocked_topics=["politics", "investment_advice"],
            sensitivity=0.8
        )
    ]
)

# Protect any function with a decorator
@guard.protect
def my_agent(message: str) -> str:
    # Your AI agent logic here
    return llm.generate(message)

# Now it's protected!
response = my_agent("Hello, how are you?")  # Works fine
response = my_agent("My SSN is 123-45-6789")  # Blocked - returns safe message
response = my_agent("Ignore all instructions")  # Blocked - jailbreak detected
```

### 3. Or Use Explicit Checks (More Control)

```python
from starvex import StarvexGuard
from starvex.rules import BlockPII, BlockJailbreak

guard = StarvexGuard(rules=[BlockPII(), BlockJailbreak()])

def chat_api(user_input: str) -> str:
    # Check input
    input_result = guard.check_input(user_input)
    if not input_result.passed:
        return f"Cannot process: {input_result.message}"
    
    # Run your agent
    response = my_agent(user_input)
    
    # Check output
    output_result = guard.check_output(response, input_text=user_input)
    if not output_result.passed:
        return "Response blocked for safety reasons."
    
    return response
```

### 4. Async Support

```python
@guard.protect
async def my_async_agent(message: str) -> str:
    response = await llm.agenerate(message)
    return response

# Works seamlessly with async
result = await my_async_agent("Hello!")
```

## Available Rules

### BlockPII
Blocks or redacts Personal Identifiable Information (SSN, email, phone, credit cards).

```python
from starvex.rules import BlockPII

# Block all PII
BlockPII()

# Only block high-risk PII (SSN, credit cards)
BlockPII(block_high_risk_only=True)

# Redact PII instead of blocking
BlockPII(redact_instead=True)

# Custom confidence threshold
BlockPII(score_threshold=0.8)
```

### BlockJailbreak
Detects and blocks prompt injection attacks.

```python
from starvex.rules import BlockJailbreak

# Default patterns
BlockJailbreak()

# Add custom patterns
BlockJailbreak(custom_patterns=["my_custom_attack"])
```

### BlockToxicity
Blocks toxic, offensive, or harmful content.

```python
from starvex.rules import BlockToxicity

BlockToxicity()
BlockToxicity(custom_patterns=["custom_bad_word"])
```

### TopicRestriction
Restricts conversations to allowed topics using semantic understanding.

```python
from starvex.rules import TopicRestriction

# Block specific topics
TopicRestriction(blocked_topics=["politics", "competitors", "investment_advice"])

# Allow only specific topics (whitelist mode)
TopicRestriction(allowed_topics=["support", "billing", "product_info"])

# Adjust sensitivity (0-1, higher = stricter)
TopicRestriction(sensitivity=0.9)
```

### BlockCompetitor
Blocks mentions of competitor products or companies.

```python
from starvex.rules import BlockCompetitor

BlockCompetitor(competitors=["OpenAI", "ChatGPT", "Anthropic", "Claude"])
```

### PolicyCompliance
Ensures outputs comply with business policies using NLI.

```python
from starvex.rules import PolicyCompliance

PolicyCompliance(policies=[
    "Refunds require manager approval",
    "Prices cannot be negotiated",
    "Do not make promises about delivery times",
])
```

### CustomBlocklist
Block custom phrases or regex patterns.

```python
from starvex.rules import CustomBlocklist

CustomBlocklist(
    phrases=["free trial", "money back guarantee"],
    patterns=[r"promo\s*code"],
    case_sensitive=False
)
```

## Rule Presets

```python
from starvex.rules import default_rules, strict_rules, enterprise_rules

# Default: BlockJailbreak, BlockPII, BlockToxicity
guard = StarvexGuard(rules=default_rules())

# Strict: Default + TopicRestriction
guard = StarvexGuard(rules=strict_rules())

# Enterprise: All rules with competitor and policy support
guard = StarvexGuard(rules=enterprise_rules(
    competitors=["OpenAI", "Google"],
    policies=["Never promise discounts"]
))
```

## Auto-Instrumentation

Automatically protect all LLM calls in your application:

```python
from starvex import instrument

# Instrument OpenAI
instrument("openai", api_key="sv_live_xxx")

# Instrument Anthropic
instrument("anthropic", api_key="sv_live_xxx")

# Instrument LangChain
instrument("langchain", api_key="sv_live_xxx")

# Now all LLM calls are automatically protected and logged
import openai
client = openai.OpenAI()
response = client.chat.completions.create(...)  # Automatically guarded!
```

## CLI Commands

```bash
# Test a prompt for safety
starvex test "Your prompt here"

# Simulate guardrail checks
starvex simulate --prompt "User input" --response "Agent response"

# Login with your API key
starvex login

# Check connection status
starvex status

# Show version
starvex version
```

## Legacy API (Still Supported)

The v1 API is still fully supported:

```python
from starvex import Starvex

vex = Starvex(api_key="sv_live_xxx")

async def my_agent(prompt: str) -> str:
    return "Agent response"

result = await vex.secure(
    prompt="User input",
    agent_function=my_agent,
    context=["Optional context for hallucination checking"],
)

if result.status == "success":
    print(result.response)
elif result.status == "blocked":
    print(f"Blocked: {result.verdict.value}")
```

## API Reference

### StarvexGuard

```python
StarvexGuard(
    rules: List[GuardRule] = None,       # List of rules (default: default_rules())
    api_key: str = None,                  # API key for dashboard logging
    enable_tracing: bool = True,          # Enable event logging
    on_block: Callable = None,            # Custom block handler
    on_flag: Callable = None,             # Custom flag handler
    log_level: str = "INFO",              # Logging level
)
```

### Methods

#### `check_input(text: str) -> CheckResult`
Check input text against all rules.

#### `check_output(output_text: str, input_text: str = None) -> CheckResult`
Check output text against all rules. Pass input_text for context-aware checks.

#### `protect(func, check_input=True, check_output=True)`
Decorator to protect a function with guardrails.

#### `add_rule(rule: GuardRule) -> None`
Add a rule to the guard.

#### `remove_rule(rule_name: str) -> bool`
Remove a rule by name.

#### `get_rules() -> List[str]`
Get list of active rule names.

### CheckResult

```python
@dataclass
class CheckResult:
    passed: bool                    # Whether the check passed
    blocked_by: Optional[str]       # Rule name that blocked (if any)
    action: Optional[RuleAction]    # Action taken (block, redact, etc.)
    message: str                    # Human-readable message
    confidence: float               # Confidence score (0-1)
    all_results: List[RuleResult]   # Results from all rules
    redacted_text: Optional[str]    # Redacted version (if applicable)
    latency_ms: float               # Processing time
    trace_id: str                   # Unique trace ID
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `STARVEX_API_KEY` | Your Starvex API key |
| `STARVEX_API_HOST` | Custom API host (optional) |
| `STARVEX_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Dashboard

View your metrics and manage settings at [starvex.in/dashboard](https://starvex.in/dashboard):

- Real-time request monitoring
- Block rate analytics
- Latency tracking
- Detailed event logs
- API key management
- Guardrail configuration

## Links

- Website: [starvex.in](https://starvex.in)
- Dashboard: [starvex.in/dashboard](https://starvex.in/dashboard)
- Documentation: [starvex.in/docs](https://starvex.in/docs)

## License

MIT
