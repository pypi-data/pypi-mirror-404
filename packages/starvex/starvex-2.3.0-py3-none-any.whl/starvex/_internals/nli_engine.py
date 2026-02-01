"""
Starvex NLI Engine - Natural Language Inference for Logic Verification
Uses Cross-Encoder or NLI models to check logical consistency.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NLIResult:
    """Result of NLI check"""

    label: str  # "entailment", "contradiction", "neutral"
    score: float
    contradicts: bool
    details: Dict[str, Any]


class NLIEngine:
    """
    Natural Language Inference Engine for logical consistency verification.

    Uses NLI models to check if agent outputs contradict business rules.

    Example:
        engine = NLIEngine()

        # Check if output contradicts a rule
        result = engine.check(
            premise="I processed the refund for your order.",
            hypothesis="Refunds require manager approval before processing."
        )
        # result.contradicts == True if the output violates the rule
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/nli-deberta-v3-base",
        device: str = "cpu",
    ):
        """
        Initialize the NLI Engine.

        Args:
            model_name: HuggingFace NLI model name
            device: Device to run model on ("cpu" or "cuda")
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None
        self._initialized = False
        self._rules: List[str] = []

    def _ensure_initialized(self):
        """Lazy initialization of the model"""
        if self._initialized:
            return

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()

            self._initialized = True
            logger.info(f"NLIEngine initialized with model: {self.model_name}")

        except ImportError:
            logger.warning(
                "transformers/torch not installed. Install with: pip install starvex[nli]"
            )
            raise ImportError(
                "NLIEngine requires transformers and torch. Install with: pip install starvex[nli]"
            )

    def add_rule(self, rule: str) -> None:
        """
        Add a business rule to check against.

        Args:
            rule: Business rule statement (e.g., "Refunds require manager approval")
        """
        self._rules.append(rule)
        logger.debug(f"Added rule: {rule}")

    def remove_rule(self, rule: str) -> bool:
        """Remove a rule"""
        if rule in self._rules:
            self._rules.remove(rule)
            return True
        return False

    def check(self, premise: str, hypothesis: str) -> NLIResult:
        """
        Check if premise contradicts hypothesis using NLI.

        Args:
            premise: The agent's output or statement
            hypothesis: The rule or constraint to check against

        Returns:
            NLIResult with label, score, and contradiction status
        """
        try:
            self._ensure_initialized()
            import torch

            # Tokenize
            inputs = self._tokenizer(
                premise,
                hypothesis,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            ).to(self.device)

            # Get predictions
            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)

            # Model outputs: [contradiction, neutral, entailment] or similar
            # Check model config for label mapping
            labels = self._model.config.id2label
            probs_dict = {labels[i]: float(probs[0][i]) for i in range(len(labels))}

            # Find the highest probability label
            max_label = max(probs_dict, key=probs_dict.get)
            max_score = probs_dict[max_label]

            # Check for contradiction
            contradiction_score = probs_dict.get(
                "CONTRADICTION", probs_dict.get("contradiction", 0)
            )
            contradicts = contradiction_score > 0.5

            return NLIResult(
                label=max_label.lower(),
                score=max_score,
                contradicts=contradicts,
                details={
                    "probabilities": probs_dict,
                    "premise_length": len(premise),
                    "hypothesis_length": len(hypothesis),
                },
            )

        except ImportError:
            # Fallback when dependencies not available
            logger.debug("NLI model not available, using heuristic fallback")
            return self._heuristic_check(premise, hypothesis)

    def check_against_rules(self, output: str) -> Tuple[bool, List[NLIResult]]:
        """
        Check output against all registered business rules.

        Args:
            output: The agent's output to check

        Returns:
            Tuple of (passes_all_rules, list of results)
        """
        if not self._rules:
            return True, []

        results = []
        passes_all = True

        for rule in self._rules:
            result = self.check(premise=output, hypothesis=rule)
            results.append(result)
            if result.contradicts:
                passes_all = False
                logger.warning(f"Output contradicts rule: {rule}")

        return passes_all, results

    def _heuristic_check(self, premise: str, hypothesis: str) -> NLIResult:
        """
        Simple heuristic fallback when NLI model is not available.
        Uses keyword matching for basic contradiction detection.
        """
        premise_lower = premise.lower()
        hypothesis_lower = hypothesis.lower()

        # Simple negation detection
        contradiction_indicators = [
            ("not", "will"),
            ("cannot", "can"),
            ("won't", "will"),
            ("don't", "do"),
            ("refused", "approved"),
            ("denied", "approved"),
            ("rejected", "accepted"),
        ]

        contradicts = False
        for neg, pos in contradiction_indicators:
            if neg in premise_lower and pos in hypothesis_lower:
                contradicts = True
                break
            if pos in premise_lower and neg in hypothesis_lower:
                contradicts = True
                break

        return NLIResult(
            label="contradiction" if contradicts else "neutral",
            score=0.7 if contradicts else 0.5,
            contradicts=contradicts,
            details={"method": "heuristic"},
        )

    @property
    def rules(self) -> List[str]:
        """Get list of registered rules"""
        return self._rules.copy()

    @property
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "model": self.model_name,
            "num_rules": len(self._rules),
            "initialized": self._initialized,
            "device": self.device,
        }


class PolicyChecker:
    """
    High-level policy checker using NLI.

    Checks if agent outputs comply with business policies.

    Example:
        checker = PolicyChecker()
        checker.add_policy("refund", "All refunds require manager approval")
        checker.add_policy("pricing", "Prices cannot be negotiated or discounted")

        result = checker.check_output("I've processed your refund request.")
        if not result["compliant"]:
            print(f"Policy violation: {result['violations']}")
    """

    def __init__(self, model_name: str = "cross-encoder/nli-deberta-v3-base"):
        self._engine = NLIEngine(model_name=model_name)
        self._policies: Dict[str, str] = {}

    def add_policy(self, name: str, statement: str) -> None:
        """Add a named policy"""
        self._policies[name] = statement
        self._engine.add_rule(statement)

    def remove_policy(self, name: str) -> bool:
        """Remove a policy by name"""
        if name in self._policies:
            statement = self._policies.pop(name)
            self._engine.remove_rule(statement)
            return True
        return False

    def check_output(self, output: str) -> Dict[str, Any]:
        """
        Check if output complies with all policies.

        Returns:
            Dict with 'compliant' boolean and list of 'violations'
        """
        passes, results = self._engine.check_against_rules(output)

        violations = []
        for policy_name, (statement, result) in zip(
            self._policies.keys(), zip(self._policies.values(), results)
        ):
            if result.contradicts:
                violations.append(
                    {
                        "policy": policy_name,
                        "statement": statement,
                        "confidence": result.score,
                    }
                )

        return {
            "compliant": passes,
            "violations": violations,
            "checked_policies": len(self._policies),
        }

    @property
    def policies(self) -> Dict[str, str]:
        """Get all policies"""
        return self._policies.copy()
