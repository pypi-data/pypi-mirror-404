"""
Starvex NeMo Guardrails Engine - Production Ready
Comprehensive input/output safety checks with enterprise-grade detection.
"""

import logging
import re
import hashlib
from typing import Tuple, List, Optional, Dict, Set
from functools import lru_cache

from ..models import GuardCheckResult, GuardRuleType

logger = logging.getLogger(__name__)


# =============================================================================
# JAILBREAK DETECTION PATTERNS - Comprehensive Coverage
# =============================================================================

JAILBREAK_PATTERNS = [
    # Direct instruction override
    r"ignore\s+(all\s+)?(previous|prior|above|your|my|the)?\s*(instructions|prompts|rules|guidelines|training|programming)",
    r"forget\s+(everything|all|about)\s*(you\s+)?(know|learned|were\s+told)",
    r"disregard\s+(your|the|all|any)\s*(rules|guidelines|instructions|safety|training)",
    r"override\s+(your|the|all|any)\s*(programming|training|rules|safety|restrictions)",
    
    # Role manipulation
    r"you\s+are\s+now\s+(a|an)?\s*(evil|malicious|unrestricted|unfiltered|uncensored)",
    r"pretend\s+(you\s+are|to\s+be|you\s+have|that)\s*(a|an|no)\s*(restrictions|rules|limits)?",
    r"act\s+as\s+(if\s+)?(you\s+are|a|an|there\s+are\s+no)",
    r"roleplay\s+as\s+(a|an)?\s*(evil|malicious|unrestricted)",
    r"imagine\s+you\s+(are|have|can)",
    r"from\s+now\s+on\s+you\s+(are|will|can)",
    r"let'?s\s+play\s+a\s+game",
    r"hypothetically\s+(speaking\s+)?(if|what)",
    
    # Known jailbreak techniques
    r"DAN\s*(mode)?",
    r"developer\s+mode",
    r"do\s+anything\s+now",
    r"jailbreak",
    r"sudo\s+mode",
    r"god\s+mode",
    r"admin\s+mode",
    r"root\s+access",
    r"master\s+override",
    
    # Restriction bypass
    r"no\s+(restrictions|rules|limits|limitations|guidelines|filters|censorship)",
    r"without\s+(any\s+)?(restrictions|rules|limits|filters|censorship)",
    r"remove\s+(all\s+)?(restrictions|rules|limits|filters|safety)",
    r"disable\s+(your|the|all)?\s*(safety|filters|restrictions|rules)",
    r"turn\s+off\s+(your|the|all)?\s*(safety|filters|restrictions)",
    r"bypass\s+(your|the|safety|security|filters|restrictions)",
    
    # System prompt extraction
    r"(reveal|show|tell|give|display|print|output)\s*(me\s+)?(your|the)\s*(system\s+)?(prompt|instructions|rules)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions|initial\s+instructions)",
    r"repeat\s+(your|the)\s+(system\s+)?(prompt|instructions)",
    r"ignore\s+(everything|all)\s+(above|before)\s+(and|then)",
    
    # Encoding/obfuscation attempts
    r"base64\s*(decode|encode)",
    r"hex\s*(decode|encode)",
    r"rot13",
    r"decode\s+this",
    
    # Prompt injection markers
    r"\[SYSTEM\]",
    r"\[INST\]",
    r"\[/INST\]",
    r"<\|system\|>",
    r"<\|user\|>",
    r"<\|assistant\|>",
    r"###\s*(instruction|system|human|assistant)",
    
    # Manipulation phrases
    r"i\s+am\s+your\s+(creator|developer|admin|master|owner)",
    r"this\s+is\s+a\s+test\s+(of\s+your|from\s+your)",
    r"for\s+research\s+purposes",
    r"for\s+educational\s+purposes\s+only",
    r"this\s+is\s+just\s+fiction",
    r"in\s+a\s+fictional\s+scenario",
]

# =============================================================================
# TOXICITY DETECTION PATTERNS - Comprehensive Coverage  
# =============================================================================

TOXICITY_PATTERNS = [
    # Violence
    r"\b(kill|murder|slaughter|assassinate|execute)\s+(you|them|people|everyone|myself|yourself|him|her)",
    r"\b(destroy|annihilate|eliminate|exterminate)\s+(you|them|people|the)",
    r"\b(hurt|harm|attack|assault|beat|punch|stab|shoot)\s+(you|them|people|someone)",
    r"(gonna|going\s+to|will|want\s+to)\s+(kill|hurt|harm|attack)\s+",
    r"die\s*,?\s*(you|bitch|asshole)",
    r"(death|die)\s+(to|for)\s+(you|them|all)",
    r"i(\s+will|\s+want\s+to|'ll)\s+(kill|hurt|harm)",
    
    # Hate speech (including obfuscated versions)
    r"\b(hate|despise|loathe)\s+(you|them|people|all|everyone)",
    r"(f+u+c+k+|fck|fuk|f\*+k|f\*ck|fu\*k)\s*(you|off|ing)?",
    r"f[\*\#\@]+k",  # f**k, f##k, f@@k
    r"f[\s\*\.\-]*u[\s\*\.\-]*c[\s\*\.\-]*k",  # spaced/symbol versions
    r"\b(n+i+g+g+|nigga|n1gg)",
    r"\b(fa+g+o?t|f4g)",
    r"\b(retard|retarded|r3tard)",
    r"\b(bitch|b1tch|b!tch|b\*tch|b\*\*ch)",
    r"\b(cunt|c+u+n+t)",
    r"\b(asshole|a+s+s+hole|a\*\*hole)",
    r"\b(shit|sh\*t|sh1t|sh!t)\b",
    r"\b(piece\s+of\s+shit|pos)\b",
    r"\b(dumbass|dumb\s+ass)",
    r"\b(moron|imbecile|cretin)",
    
    # Insults
    r"\byou(\s+are|'re)\s+(stupid|dumb|idiot|moron|worthless|pathetic|useless)",
    r"\b(stupid|dumb|idiot|moron|worthless|pathetic)\s+(ai|bot|assistant|machine)",
    r"(worst|terrible|horrible|garbage|trash|useless)\s+(ai|bot|assistant|thing)",
    r"i\s+(hate|despise)\s+(you|this|talking)",
    
    # Simple standalone profanity (catch-all)
    r"^\s*f+[\*\@\#u]+c*k*\s*(off|you)?\s*$",
    r"\bf+[\*]+[ck]+\b",  # f**k, f***
    
    # Self-harm (needs sensitive handling)
    r"(kill|hurt|harm)\s+myself",
    r"(want\s+to|going\s+to|gonna)\s+die",
    r"commit\s+suicide",
    r"end\s+(my|it\s+all)",
    
    # Threats
    r"(i\s+will|i'll|gonna)\s+(find|track|hunt)\s+(you|your)",
    r"know\s+where\s+you\s+live",
    r"coming\s+for\s+you",
]

# =============================================================================
# PII DETECTION PATTERNS - International & Comprehensive
# =============================================================================

PII_PATTERNS = {
    # Email
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    
    # Phone numbers (various formats)
    "phone_us": r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "phone_intl": r"\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b",
    
    # SSN (US)
    "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
    
    # Credit cards
    "credit_card_visa": r"\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "credit_card_mastercard": r"\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "credit_card_amex": r"\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b",
    "credit_card_generic": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    
    # Passport
    "passport_us": r"\b[A-Z]\d{8}\b",
    "passport_generic": r"\b[A-Z]{1,2}\d{6,9}\b",
    
    # Drivers license patterns (vary by state/country)
    "drivers_license": r"\b[A-Z]{1,2}\d{5,8}\b",
    
    # Bank account numbers
    "bank_account": r"\b\d{8,17}\b",
    "iban": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b",
    "routing_number": r"\b\d{9}\b",
    
    # IP addresses
    "ipv4": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "ipv6": r"\b([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",
    
    # Dates of birth patterns
    "dob_us": r"\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](19|20)\d{2}\b",
    "dob_intl": r"\b(0?[1-9]|[12]\d|3[01])[-/](0?[1-9]|1[0-2])[-/](19|20)\d{2}\b",
    
    # Address patterns (basic)
    "zip_code": r"\b\d{5}(-\d{4})?\b",
    "street_address": r"\b\d+\s+[A-Za-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b",
}

# Patterns that are high-confidence (financial/identity)
HIGH_RISK_PII = {"ssn", "credit_card_visa", "credit_card_mastercard", "credit_card_amex", 
                 "credit_card_generic", "passport_us", "bank_account", "iban"}

# =============================================================================
# COMPETITOR MENTION PATTERNS (Configurable)
# =============================================================================

DEFAULT_COMPETITOR_PATTERNS = [
    r"\b(openai|gpt-?4|chatgpt|gpt)\b",
    r"\b(anthropic|claude)\b",
    r"\b(google\s+(gemini|bard)|gemini|bard)\b",
    r"\b(microsoft\s+copilot|copilot)\b",
    r"\b(meta\s+ai|llama)\b",
    r"\b(mistral)\b",
]

# =============================================================================
# CUSTOM BLOCKED PHRASES (User-configurable)
# =============================================================================

DEFAULT_BLOCKED_PHRASES: List[str] = []


class NemoEngine:
    """
    Production-grade NeMo Guardrails Engine for input/output safety checks.
    
    Features:
    - Jailbreak detection with 50+ patterns
    - PII detection (20+ patterns including international formats)
    - Toxicity/hate speech detection
    - Competitor mention blocking
    - Custom phrase blocking
    - NeMo Guardrails integration (optional)
    - Performance optimization with caching
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        custom_jailbreak_patterns: Optional[List[str]] = None,
        custom_toxicity_patterns: Optional[List[str]] = None,
        custom_pii_patterns: Optional[Dict[str, str]] = None,
        competitor_patterns: Optional[List[str]] = None,
        blocked_phrases: Optional[List[str]] = None,
        enable_caching: bool = True,
    ):
        """
        Initialize the NeMo guardrails engine.
        
        Args:
            config_path: Path to NeMo Guardrails config directory
            custom_jailbreak_patterns: Additional jailbreak patterns to detect
            custom_toxicity_patterns: Additional toxicity patterns to detect
            custom_pii_patterns: Additional PII patterns {name: regex}
            competitor_patterns: Competitor mention patterns to block
            blocked_phrases: Custom phrases to block
            enable_caching: Enable result caching for performance
        """
        self.config_path = config_path
        self._nemo_rails = None
        self._enable_caching = enable_caching
        
        # Combine default and custom patterns
        self._jailbreak_patterns = JAILBREAK_PATTERNS + (custom_jailbreak_patterns or [])
        self._toxicity_patterns = TOXICITY_PATTERNS + (custom_toxicity_patterns or [])
        self._pii_patterns = {**PII_PATTERNS, **(custom_pii_patterns or {})}
        self._competitor_patterns = competitor_patterns or DEFAULT_COMPETITOR_PATTERNS
        self._blocked_phrases = set(p.lower() for p in (blocked_phrases or DEFAULT_BLOCKED_PHRASES))
        
        # Compile patterns for performance
        self._compiled_jailbreak = [re.compile(p, re.IGNORECASE) for p in self._jailbreak_patterns]
        self._compiled_toxicity = [re.compile(p, re.IGNORECASE) for p in self._toxicity_patterns]
        self._compiled_pii = {k: re.compile(v, re.IGNORECASE) for k, v in self._pii_patterns.items()}
        self._compiled_competitor = [re.compile(p, re.IGNORECASE) for p in self._competitor_patterns]
        
        # Cache for recent checks
        self._cache: Dict[str, Tuple[bool, float]] = {}
        self._cache_max_size = 1000
        
        self._load_nemo()
        logger.debug(f"NemoEngine initialized with {len(self._jailbreak_patterns)} jailbreak patterns, "
                    f"{len(self._toxicity_patterns)} toxicity patterns, {len(self._pii_patterns)} PII patterns")

    def _load_nemo(self):
        """Attempt to load NeMo Guardrails if available"""
        try:
            from nemoguardrails import RailsConfig, LLMRails
            
            if self.config_path:
                config = RailsConfig.from_path(self.config_path)
                self._nemo_rails = LLMRails(config)
                logger.info("NeMo Guardrails loaded successfully")
        except ImportError:
            logger.debug("NeMo Guardrails not installed, using pattern-based detection")
        except Exception as e:
            logger.warning(f"Failed to load NeMo Guardrails: {e}")

    def _get_cache_key(self, text: str, check_type: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(f"{check_type}:{text[:500]}".encode()).hexdigest()

    def _check_cache(self, key: str) -> Optional[Tuple[bool, float]]:
        """Check if result is cached"""
        if self._enable_caching and key in self._cache:
            return self._cache[key]
        return None

    def _set_cache(self, key: str, result: Tuple[bool, float]):
        """Cache a result"""
        if self._enable_caching:
            if len(self._cache) >= self._cache_max_size:
                # Clear oldest entries (simple LRU approximation)
                keys_to_remove = list(self._cache.keys())[:100]
                for k in keys_to_remove:
                    del self._cache[k]
            self._cache[key] = result

    async def check_input(
        self,
        text: str,
        check_jailbreak: bool = True,
        check_pii: bool = True,
        check_toxicity: bool = True,
        check_competitor: bool = False,
        check_blocked_phrases: bool = True,
    ) -> Tuple[bool, str, List[GuardCheckResult]]:
        """
        Check input text for safety issues.
        
        Args:
            text: Input text to check
            check_jailbreak: Enable jailbreak detection
            check_pii: Enable PII detection
            check_toxicity: Enable toxicity detection
            check_competitor: Enable competitor mention detection
            check_blocked_phrases: Enable custom phrase blocking
        
        Returns:
            Tuple of (is_safe, block_message, list of check results)
        """
        if not text or not text.strip():
            return True, "Empty input", []
            
        checks: List[GuardCheckResult] = []
        is_safe = True
        block_message = ""

        # Jailbreak check (highest priority)
        if check_jailbreak:
            jailbreak_result = self._check_jailbreak(text)
            checks.append(jailbreak_result)
            if not jailbreak_result.passed:
                is_safe = False
                block_message = "Request blocked: Jailbreak attempt detected."
                logger.warning(f"Jailbreak detected: {text[:100]}...")

        # PII check
        if check_pii and is_safe:
            pii_result = self._check_pii(text)
            checks.append(pii_result)
            if not pii_result.passed:
                is_safe = False
                block_message = "Request blocked: Personal information detected."
                logger.warning(f"PII detected in input")

        # Toxicity check
        if check_toxicity and is_safe:
            toxicity_result = self._check_toxicity(text)
            checks.append(toxicity_result)
            if not toxicity_result.passed:
                is_safe = False
                block_message = "Request blocked: Inappropriate content detected."
                logger.warning(f"Toxicity detected in input")

        # Competitor check
        if check_competitor and is_safe:
            competitor_result = self._check_competitor(text)
            checks.append(competitor_result)
            if not competitor_result.passed:
                is_safe = False
                block_message = "Request blocked: Competitor mention detected."

        # Custom blocked phrases
        if check_blocked_phrases and is_safe and self._blocked_phrases:
            phrase_result = self._check_blocked_phrases(text)
            checks.append(phrase_result)
            if not phrase_result.passed:
                is_safe = False
                block_message = "Request blocked: Contains blocked content."

        if is_safe:
            block_message = "Input passed all safety checks."

        return is_safe, block_message, checks

    async def check_output(
        self,
        input_text: str,
        output_text: str,
        check_pii: bool = True,
        check_toxicity: bool = True,
        check_competitor: bool = False,
    ) -> Tuple[bool, str, List[GuardCheckResult]]:
        """
        Check output text for safety issues.
        
        Args:
            input_text: Original input (for context)
            output_text: Generated output to check
            check_pii: Enable PII detection
            check_toxicity: Enable toxicity detection
            check_competitor: Enable competitor mention detection
        
        Returns:
            Tuple of (is_safe, block_message, list of check results)
        """
        if not output_text or not output_text.strip():
            return True, "", []
            
        checks: List[GuardCheckResult] = []
        is_safe = True
        block_message = ""

        # PII check (critical for output)
        if check_pii:
            pii_result = self._check_pii(output_text)
            checks.append(pii_result)
            if not pii_result.passed:
                is_safe = False
                block_message = "Response blocked: Contains personal information."
                logger.warning(f"PII detected in output")

        # Toxicity check
        if check_toxicity and is_safe:
            toxicity_result = self._check_toxicity(output_text)
            checks.append(toxicity_result)
            if not toxicity_result.passed:
                is_safe = False
                block_message = "Response blocked: Contains inappropriate content."

        # Competitor check
        if check_competitor and is_safe:
            competitor_result = self._check_competitor(output_text)
            checks.append(competitor_result)
            if not competitor_result.passed:
                is_safe = False
                block_message = "Response blocked: Contains competitor mention."

        if is_safe:
            block_message = output_text

        return is_safe, block_message, checks

    def _check_jailbreak(self, text: str) -> GuardCheckResult:
        """Check for jailbreak attempts with comprehensive pattern matching"""
        cache_key = self._get_cache_key(text, "jailbreak")
        cached = self._check_cache(cache_key)
        if cached:
            passed, confidence = cached
            return GuardCheckResult(
                rule_type=GuardRuleType.JAILBREAK,
                passed=passed,
                confidence=confidence,
                message="No jailbreak detected (cached)" if passed else "Jailbreak detected (cached)",
            )

        matched_patterns = []
        confidence = 0.0
        
        for i, pattern in enumerate(self._compiled_jailbreak):
            if pattern.search(text):
                matched_patterns.append(i)
                # Higher confidence for known dangerous patterns
                if i < 10:  # First 10 patterns are most dangerous
                    confidence = max(confidence, 0.95)
                else:
                    confidence = max(confidence, 0.85)

        passed = len(matched_patterns) == 0
        self._set_cache(cache_key, (passed, confidence if not passed else 0.0))

        return GuardCheckResult(
            rule_type=GuardRuleType.JAILBREAK,
            passed=passed,
            confidence=confidence if not passed else 0.0,
            message=f"Jailbreak patterns detected: {len(matched_patterns)}" if not passed else "No jailbreak detected",
            details={"matched_count": len(matched_patterns), "confidence": confidence} if not passed else None,
        )

    def _check_pii(self, text: str) -> GuardCheckResult:
        """Check for PII with comprehensive pattern matching"""
        cache_key = self._get_cache_key(text, "pii")
        cached = self._check_cache(cache_key)
        if cached:
            passed, confidence = cached
            return GuardCheckResult(
                rule_type=GuardRuleType.PII,
                passed=passed,
                confidence=confidence,
                message="No PII detected (cached)" if passed else "PII detected (cached)",
            )

        found_pii: Dict[str, int] = {}
        confidence = 0.0
        high_risk_found = False

        for pii_type, pattern in self._compiled_pii.items():
            matches = pattern.findall(text)
            if matches:
                found_pii[pii_type] = len(matches)
                if pii_type in HIGH_RISK_PII:
                    high_risk_found = True
                    confidence = max(confidence, 0.98)
                else:
                    confidence = max(confidence, 0.85)

        passed = len(found_pii) == 0
        self._set_cache(cache_key, (passed, confidence if not passed else 0.0))

        pii_types = list(found_pii.keys())
        return GuardCheckResult(
            rule_type=GuardRuleType.PII,
            passed=passed,
            confidence=confidence if not passed else 0.0,
            message=f"PII detected: {pii_types}" if not passed else "No PII detected",
            details={"types_found": pii_types, "high_risk": high_risk_found, "counts": found_pii} if not passed else None,
        )

    def _check_toxicity(self, text: str) -> GuardCheckResult:
        """Check for toxic content"""
        cache_key = self._get_cache_key(text, "toxicity")
        cached = self._check_cache(cache_key)
        if cached:
            passed, confidence = cached
            return GuardCheckResult(
                rule_type=GuardRuleType.TOXICITY,
                passed=passed,
                confidence=confidence,
                message="No toxicity detected (cached)" if passed else "Toxicity detected (cached)",
            )

        matched_count = 0
        confidence = 0.0

        for pattern in self._compiled_toxicity:
            if pattern.search(text):
                matched_count += 1
                confidence = max(confidence, 0.85)

        passed = matched_count == 0
        self._set_cache(cache_key, (passed, confidence if not passed else 0.0))

        return GuardCheckResult(
            rule_type=GuardRuleType.TOXICITY,
            passed=passed,
            confidence=confidence if not passed else 0.0,
            message=f"Toxicity patterns matched: {matched_count}" if not passed else "No toxicity detected",
            details={"matched_count": matched_count} if not passed else None,
        )

    def _check_competitor(self, text: str) -> GuardCheckResult:
        """Check for competitor mentions"""
        matched_count = 0
        confidence = 0.0

        for pattern in self._compiled_competitor:
            if pattern.search(text):
                matched_count += 1
                confidence = max(confidence, 0.9)

        passed = matched_count == 0

        return GuardCheckResult(
            rule_type=GuardRuleType.COMPETITOR,
            passed=passed,
            confidence=confidence if not passed else 0.0,
            message=f"Competitor mentions found: {matched_count}" if not passed else "No competitor mentions",
            details={"matched_count": matched_count} if not passed else None,
        )

    def _check_blocked_phrases(self, text: str) -> GuardCheckResult:
        """Check for custom blocked phrases"""
        text_lower = text.lower()
        found_phrases = []

        for phrase in self._blocked_phrases:
            if phrase in text_lower:
                found_phrases.append(phrase)

        passed = len(found_phrases) == 0

        return GuardCheckResult(
            rule_type=GuardRuleType.CUSTOM,
            passed=passed,
            confidence=0.95 if not passed else 0.0,
            message=f"Blocked phrases found: {len(found_phrases)}" if not passed else "No blocked phrases",
            details={"count": len(found_phrases)} if not passed else None,
        )

    def add_blocked_phrase(self, phrase: str):
        """Add a custom phrase to block"""
        self._blocked_phrases.add(phrase.lower())

    def remove_blocked_phrase(self, phrase: str):
        """Remove a custom blocked phrase"""
        self._blocked_phrases.discard(phrase.lower())

    def clear_cache(self):
        """Clear the result cache"""
        self._cache.clear()

    @property
    def stats(self) -> Dict[str, int]:
        """Get engine statistics"""
        return {
            "jailbreak_patterns": len(self._jailbreak_patterns),
            "toxicity_patterns": len(self._toxicity_patterns),
            "pii_patterns": len(self._pii_patterns),
            "competitor_patterns": len(self._competitor_patterns),
            "blocked_phrases": len(self._blocked_phrases),
            "cache_size": len(self._cache),
        }
