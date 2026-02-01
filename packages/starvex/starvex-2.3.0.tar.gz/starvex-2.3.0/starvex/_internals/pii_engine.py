"""
Starvex PII Engine - Enterprise-grade PII Detection
Uses Microsoft Presidio for high-accuracy PII detection.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PIIEntity:
    """Detected PII entity"""

    entity_type: str
    text: str
    start: int
    end: int
    score: float


@dataclass
class PIIResult:
    """Result of PII detection"""

    has_pii: bool
    entities: List[PIIEntity]
    high_risk: bool
    anonymized_text: Optional[str] = None


# High-risk PII types that should always be blocked
HIGH_RISK_TYPES = {
    "CREDIT_CARD",
    "CRYPTO",
    "US_SSN",
    "US_BANK_NUMBER",
    "US_ITIN",
    "UK_NHS",
    "US_PASSPORT",
    "IBAN_CODE",
}

# Medium-risk PII types that may need context
MEDIUM_RISK_TYPES = {
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_DRIVER_LICENSE",
    "IP_ADDRESS",
    "DATE_TIME",
}


class PIIEngine:
    """
    Enterprise PII Detection Engine using Microsoft Presidio.

    Provides high-accuracy PII detection with ML-based entity recognition.
    Falls back to regex patterns if Presidio is not available.

    Example:
        engine = PIIEngine()
        result = engine.detect("My SSN is 123-45-6789 and email is john@example.com")

        if result.has_pii:
            print(f"Found PII: {[e.entity_type for e in result.entities]}")
            print(f"Anonymized: {result.anonymized_text}")
    """

    def __init__(
        self,
        languages: List[str] = None,
        score_threshold: float = 0.5,
        enable_anonymization: bool = True,
    ):
        """
        Initialize the PII Engine.

        Args:
            languages: List of languages to support (default: ["en"])
            score_threshold: Minimum confidence score for PII detection
            enable_anonymization: Whether to generate anonymized text
        """
        self.languages = languages or ["en"]
        self.score_threshold = score_threshold
        self.enable_anonymization = enable_anonymization

        self._analyzer = None
        self._anonymizer = None
        self._initialized = False
        self._use_presidio = False

        # Custom entity patterns for fallback
        self._custom_patterns = self._get_fallback_patterns()

    def _ensure_initialized(self):
        """Lazy initialization of Presidio"""
        if self._initialized:
            return

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine

            self._analyzer = AnalyzerEngine()
            self._anonymizer = AnonymizerEngine()
            self._use_presidio = True
            self._initialized = True

            logger.info("PIIEngine initialized with Microsoft Presidio")

        except ImportError:
            logger.warning(
                "presidio-analyzer not installed, using regex fallback. "
                "Install with: pip install starvex[pii]"
            )
            self._use_presidio = False
            self._initialized = True

    def _get_fallback_patterns(self) -> Dict[str, str]:
        """Get regex patterns for fallback detection"""
        return {
            "EMAIL_ADDRESS": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "PHONE_NUMBER": r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "US_SSN": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            "CREDIT_CARD": r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))\d{12}\b|\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "IP_ADDRESS": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "IBAN_CODE": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b",
            "US_PASSPORT": r"\b[A-Z]\d{8}\b",
            "DATE_TIME": r"\b(0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])[-/](19|20)\d{2}\b",
        }

    def detect(self, text: str) -> PIIResult:
        """
        Detect PII in text.

        Args:
            text: Text to analyze

        Returns:
            PIIResult with detected entities and anonymized text
        """
        self._ensure_initialized()

        if self._use_presidio:
            return self._detect_with_presidio(text)
        else:
            return self._detect_with_regex(text)

    def _detect_with_presidio(self, text: str) -> PIIResult:
        """Detect PII using Microsoft Presidio"""
        from presidio_anonymizer.entities import OperatorConfig

        # Analyze text
        results = self._analyzer.analyze(
            text=text,
            language=self.languages[0],
            score_threshold=self.score_threshold,
        )

        entities = []
        high_risk = False

        for result in results:
            entity = PIIEntity(
                entity_type=result.entity_type,
                text=text[result.start : result.end],
                start=result.start,
                end=result.end,
                score=result.score,
            )
            entities.append(entity)

            if result.entity_type in HIGH_RISK_TYPES:
                high_risk = True

        # Anonymize if enabled
        anonymized_text = None
        if self.enable_anonymization and entities:
            anonymized_result = self._anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators={
                    "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
                },
            )
            anonymized_text = anonymized_result.text

        return PIIResult(
            has_pii=len(entities) > 0,
            entities=entities,
            high_risk=high_risk,
            anonymized_text=anonymized_text,
        )

    def _detect_with_regex(self, text: str) -> PIIResult:
        """Fallback PII detection using regex patterns"""
        entities = []
        high_risk = False
        anonymized_text = text

        for entity_type, pattern in self._custom_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = PIIEntity(
                    entity_type=entity_type,
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    score=0.85,  # Fixed score for regex
                )
                entities.append(entity)

                if entity_type in HIGH_RISK_TYPES:
                    high_risk = True

        # Simple anonymization - replace from end to start to preserve indices
        if self.enable_anonymization and entities:
            sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
            for entity in sorted_entities:
                anonymized_text = (
                    anonymized_text[: entity.start]
                    + f"[{entity.entity_type}]"
                    + anonymized_text[entity.end :]
                )

        return PIIResult(
            has_pii=len(entities) > 0,
            entities=entities,
            high_risk=high_risk,
            anonymized_text=anonymized_text if entities else None,
        )

    def redact(self, text: str) -> str:
        """
        Redact all PII from text.

        Args:
            text: Text to redact

        Returns:
            Text with PII replaced by placeholders
        """
        result = self.detect(text)
        return result.anonymized_text or text

    def get_entity_types(self, text: str) -> List[str]:
        """Get list of PII entity types found in text"""
        result = self.detect(text)
        return list(set(e.entity_type for e in result.entities))

    def is_high_risk(self, text: str) -> bool:
        """Check if text contains high-risk PII"""
        result = self.detect(text)
        return result.high_risk

    @property
    def supported_entities(self) -> List[str]:
        """Get list of supported PII entity types"""
        self._ensure_initialized()

        if self._use_presidio:
            return self._analyzer.get_supported_entities()
        else:
            return list(self._custom_patterns.keys())

    @property
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "use_presidio": self._use_presidio,
            "languages": self.languages,
            "score_threshold": self.score_threshold,
            "supported_entities": len(self.supported_entities),
            "initialized": self._initialized,
        }


class PIIGuard:
    """
    High-level PII Guard for easy integration.

    Example:
        guard = PIIGuard()

        # Check input
        if guard.contains_pii(user_input):
            return "Please don't share personal information"

        # Get redacted version
        safe_text = guard.redact(user_input)
    """

    def __init__(
        self,
        block_high_risk: bool = True,
        block_all_pii: bool = False,
        redact_pii: bool = False,
    ):
        """
        Initialize PII Guard.

        Args:
            block_high_risk: Block high-risk PII (SSN, credit cards, etc.)
            block_all_pii: Block any PII detected
            redact_pii: Redact PII instead of blocking
        """
        self._engine = PIIEngine()
        self.block_high_risk = block_high_risk
        self.block_all_pii = block_all_pii
        self.redact_pii = redact_pii

    def check(self, text: str) -> Tuple[bool, Optional[str], PIIResult]:
        """
        Check text for PII.

        Returns:
            Tuple of (is_safe, redacted_text_if_applicable, full_result)
        """
        result = self._engine.detect(text)

        if not result.has_pii:
            return True, None, result

        # Check blocking rules
        should_block = False
        if self.block_all_pii:
            should_block = True
        elif self.block_high_risk and result.high_risk:
            should_block = True

        if self.redact_pii and not should_block:
            return True, result.anonymized_text, result

        return not should_block, result.anonymized_text, result

    def contains_pii(self, text: str) -> bool:
        """Check if text contains any PII"""
        result = self._engine.detect(text)
        return result.has_pii

    def redact(self, text: str) -> str:
        """Redact all PII from text"""
        return self._engine.redact(text)
