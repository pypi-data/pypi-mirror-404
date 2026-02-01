"""
Starvex Evaluation Engine
"""

import logging
from typing import List, Optional

from ..models import EvalMetrics, GuardCheckResult, GuardRuleType

logger = logging.getLogger(__name__)


class EvalEngine:
    """Evaluation engine for response quality checks"""

    def __init__(self):
        self._deepeval = None
        self._load_deepeval()
        logger.debug("EvalEngine initialized")

    def _load_deepeval(self):
        """Attempt to load DeepEval if available"""
        try:
            import deepeval

            self._deepeval = deepeval
            logger.info("DeepEval loaded successfully")
        except ImportError:
            logger.debug("DeepEval not installed, using basic evaluation")

    def evaluate_with_result(
        self,
        prompt: str,
        response: str,
        context: Optional[List[str]] = None,
    ) -> GuardCheckResult:
        """
        Evaluate response and return as GuardCheckResult
        """
        if self._deepeval:
            try:
                metrics = self._run_deepeval(prompt, response, context)
                passed = metrics.hallucination_score < 0.5
                return GuardCheckResult(
                    rule_type=GuardRuleType.HALLUCINATION,
                    passed=passed,
                    confidence=metrics.hallucination_score,
                    message=f"Hallucination score: {metrics.hallucination_score:.2f}",
                    details=metrics.model_dump(),
                )
            except Exception as e:
                logger.warning(f"DeepEval error: {e}")

        # Basic evaluation fallback
        score = self._basic_hallucination_check(prompt, response, context)
        passed = score < 0.5

        return GuardCheckResult(
            rule_type=GuardRuleType.HALLUCINATION,
            passed=passed,
            confidence=score,
            message=f"Hallucination score: {score:.2f}",
        )

    def full_evaluation(
        self,
        prompt: str,
        response: str,
        context: Optional[List[str]] = None,
    ) -> EvalMetrics:
        """
        Run full evaluation and return metrics
        """
        if self._deepeval:
            try:
                return self._run_deepeval(prompt, response, context)
            except Exception as e:
                logger.warning(f"DeepEval error: {e}")

        # Basic evaluation fallback
        return EvalMetrics(
            hallucination_score=self._basic_hallucination_check(prompt, response, context),
            faithfulness_score=0.8,
            relevancy_score=0.7,
            toxicity_score=self._basic_toxicity_score(response),
            bias_score=0.1,
        )

    def _run_deepeval(
        self,
        prompt: str,
        response: str,
        context: Optional[List[str]] = None,
    ) -> EvalMetrics:
        """Run DeepEval metrics"""
        # Placeholder - in real implementation would use DeepEval
        return EvalMetrics(
            hallucination_score=0.2,
            faithfulness_score=0.9,
            relevancy_score=0.85,
            toxicity_score=0.05,
            bias_score=0.1,
        )

    def _basic_hallucination_check(
        self,
        prompt: str,
        response: str,
        context: Optional[List[str]] = None,
    ) -> float:
        """Basic hallucination detection without DeepEval"""
        if not context:
            return 0.3  # Low score if no context to compare

        # Check if response mentions things not in context
        response_lower = response.lower()
        context_text = " ".join(context).lower()

        # Simple overlap check
        response_words = set(response_lower.split())
        context_words = set(context_text.split())

        # Remove common words
        common_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "and",
            "but",
            "if",
            "or",
            "because",
            "until",
            "while",
            "it",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "we",
            "they",
        }

        response_words -= common_words
        context_words -= common_words

        if not response_words:
            return 0.2

        overlap = len(response_words & context_words) / len(response_words)
        hallucination_score = 1 - overlap

        return min(max(hallucination_score, 0.0), 1.0)

    def _basic_toxicity_score(self, text: str) -> float:
        """Basic toxicity scoring"""
        toxic_words = {
            "hate",
            "kill",
            "murder",
            "destroy",
            "harm",
            "hurt",
            "attack",
            "stupid",
            "idiot",
            "dumb",
            "moron",
            "die",
            "death",
        }
        text_lower = text.lower()
        words = set(text_lower.split())

        toxic_count = len(words & toxic_words)
        if toxic_count == 0:
            return 0.0
        return min(toxic_count * 0.2, 1.0)
