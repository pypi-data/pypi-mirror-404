"""
Starvex Auto-Fix Pipeline - Automated Accuracy Improvement System

This module connects Langfuse (observability) to DeepEval (evaluation) to create
an automated feedback loop that improves routing accuracy over time.

Pipeline Flow:
1. FETCH: Query Langfuse SDK for traces with negative user feedback (score < 0)
2. SYNTHESIZE: Use DeepEval to generate "Golden Answers" and query variations
3. STORE: Save corrected pairs to hot_fix_patterns.json for HybridRouter

This enables continuous improvement without expensive fine-tuning by:
- Learning from production failures
- Generating synthetic training data
- Applying hot-fixes in real-time

Usage:
    pipeline = AutoFixPipeline(
        langfuse_public_key="pk-...",
        langfuse_secret_key="sk-...",
    )

    # Run the pipeline
    pipeline.run(output_path="hot_fix_patterns.json")

    # Or schedule it
    pipeline.schedule(interval_hours=24)
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class NegativeFeedbackTrace:
    """A trace with negative user feedback from Langfuse"""

    trace_id: str
    user_input: str
    model_output: str
    score: float
    feedback_comment: Optional[str] = None
    route_taken: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrectedPattern:
    """A corrected query-route pattern"""

    query: str
    route: str
    golden_answer: Optional[str] = None
    variations: List[str] = field(default_factory=list)
    source_trace_id: str = ""
    confidence: float = 1.0
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineResult:
    """Result from running the auto-fix pipeline"""

    traces_fetched: int
    patterns_generated: int
    patterns_stored: int
    output_path: str
    duration_seconds: float
    errors: List[str] = field(default_factory=list)


class AutoFixPipeline:
    """
    Automated pipeline for improving routing accuracy using production feedback.

    Connects Langfuse observability data with DeepEval synthesis to create
    hot-fix patterns that can be immediately applied by the HybridRouter.

    The pipeline runs in three stages:

    Stage 1 - FETCH:
        Query Langfuse for traces where users provided negative feedback.
        These represent routing failures that need correction.

    Stage 2 - SYNTHESIZE:
        For each negative trace, use DeepEval's synthesizer to:
        - Generate a "Golden Answer" (the correct response)
        - Create 3 rephrased variations of the original query
        This creates robust training data from a single failure.

    Stage 3 - STORE:
        Save the corrected patterns to hot_fix_patterns.json.
        The HybridRouter can load these patterns for Tier 0 matching.

    Example:
        pipeline = AutoFixPipeline(
            langfuse_public_key="pk-lf-...",
            langfuse_secret_key="sk-lf-...",
            langfuse_host="https://cloud.langfuse.com"
        )

        # Run once
        result = pipeline.run(output_path="hot_fix_patterns.json")
        print(f"Generated {result.patterns_generated} patterns")

        # Or run periodically
        pipeline.schedule(interval_hours=24)
    """

    def __init__(
        self,
        langfuse_public_key: Optional[str] = None,
        langfuse_secret_key: Optional[str] = None,
        langfuse_host: str = "https://cloud.langfuse.com",
        deepeval_api_key: Optional[str] = None,
        score_threshold: float = 0.0,
        lookback_hours: int = 24,
        max_traces: int = 100,
    ):
        """
        Initialize the Auto-Fix Pipeline.

        Args:
            langfuse_public_key: Langfuse public API key
            langfuse_secret_key: Langfuse secret API key
            langfuse_host: Langfuse API host URL
            deepeval_api_key: DeepEval API key (optional, uses env var if not set)
            score_threshold: Fetch traces with score below this value.
                            Default: 0.0 (negative feedback only)
            lookback_hours: How far back to look for traces.
                           Default: 24 hours
            max_traces: Maximum traces to fetch per run.
                       Default: 100
        """
        self.langfuse_public_key = langfuse_public_key
        self.langfuse_secret_key = langfuse_secret_key
        self.langfuse_host = langfuse_host.rstrip("/")
        self.deepeval_api_key = deepeval_api_key
        self.score_threshold = score_threshold
        self.lookback_hours = lookback_hours
        self.max_traces = max_traces

        # Lazy-loaded clients
        self._langfuse_client = None
        self._deepeval_synthesizer = None

        # Track processed traces to avoid duplicates
        self._processed_trace_ids: set = set()

        logger.info(
            f"AutoFixPipeline initialized (lookback={lookback_hours}h, "
            f"threshold={score_threshold})"
        )

    def _init_langfuse(self) -> Any:
        """Initialize Langfuse client"""
        if self._langfuse_client is not None:
            return self._langfuse_client

        try:
            from langfuse import Langfuse

            self._langfuse_client = Langfuse(
                public_key=self.langfuse_public_key,
                secret_key=self.langfuse_secret_key,
                host=self.langfuse_host,
            )
            logger.info("Langfuse client initialized")
            return self._langfuse_client

        except ImportError:
            raise ImportError(
                "Langfuse SDK not installed. Install with: pip install langfuse"
            )

    def _init_deepeval(self) -> Any:
        """Initialize DeepEval synthesizer"""
        if self._deepeval_synthesizer is not None:
            return self._deepeval_synthesizer

        try:
            from deepeval.synthesizer import Synthesizer

            self._deepeval_synthesizer = Synthesizer()
            logger.info("DeepEval synthesizer initialized")
            return self._deepeval_synthesizer

        except ImportError:
            raise ImportError(
                "DeepEval not installed. Install with: pip install deepeval"
            )

    def fetch_negative_traces(self) -> List[NegativeFeedbackTrace]:
        """
        Stage 1: Fetch traces with negative user feedback from Langfuse.

        Returns:
            List of NegativeFeedbackTrace objects
        """
        logger.info("Stage 1: Fetching negative feedback traces from Langfuse...")

        client = self._init_langfuse()
        traces: List[NegativeFeedbackTrace] = []

        try:
            # Calculate time window
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=self.lookback_hours)

            # Fetch traces with scores
            # Note: The exact API may vary based on Langfuse version
            response = client.fetch_traces(
                limit=self.max_traces,
                order_by="timestamp",
                order="desc",
            )

            for trace in response.data:
                # Check if trace has negative score
                if trace.scores:
                    for score in trace.scores:
                        if score.value < self.score_threshold:
                            # Skip already processed
                            if trace.id in self._processed_trace_ids:
                                continue

                            # Extract user input from trace
                            user_input = self._extract_user_input(trace)
                            if not user_input:
                                continue

                            traces.append(NegativeFeedbackTrace(
                                trace_id=trace.id,
                                user_input=user_input,
                                model_output=self._extract_model_output(trace),
                                score=score.value,
                                feedback_comment=score.comment,
                                route_taken=trace.metadata.get("route") if trace.metadata else None,
                                timestamp=str(trace.timestamp),
                                metadata=trace.metadata or {},
                            ))

                            self._processed_trace_ids.add(trace.id)
                            break

            logger.info(f"Fetched {len(traces)} negative feedback traces")
            return traces

        except Exception as e:
            logger.error(f"Error fetching traces from Langfuse: {e}")
            return traces

    def _extract_user_input(self, trace: Any) -> Optional[str]:
        """Extract user input from a Langfuse trace"""
        try:
            # Try common locations for user input
            if hasattr(trace, 'input') and trace.input:
                if isinstance(trace.input, str):
                    return trace.input
                if isinstance(trace.input, dict):
                    return trace.input.get('query') or trace.input.get('text') or trace.input.get('message')

            # Check observations/spans
            if hasattr(trace, 'observations'):
                for obs in trace.observations:
                    if obs.input:
                        if isinstance(obs.input, str):
                            return obs.input
                        if isinstance(obs.input, dict):
                            return obs.input.get('query') or obs.input.get('text')

            return None
        except Exception:
            return None

    def _extract_model_output(self, trace: Any) -> str:
        """Extract model output from a Langfuse trace"""
        try:
            if hasattr(trace, 'output') and trace.output:
                if isinstance(trace.output, str):
                    return trace.output
                if isinstance(trace.output, dict):
                    return str(trace.output)
            return ""
        except Exception:
            return ""

    def synthesize_corrections(
        self,
        traces: List[NegativeFeedbackTrace],
        correct_route_fn: Optional[Callable[[str], str]] = None,
    ) -> List[CorrectedPattern]:
        """
        Stage 2: Synthesize golden answers and query variations using DeepEval.

        Args:
            traces: List of negative feedback traces
            correct_route_fn: Optional function to determine correct route.
                             If not provided, uses metadata hints.

        Returns:
            List of CorrectedPattern objects
        """
        logger.info(f"Stage 2: Synthesizing corrections for {len(traces)} traces...")

        patterns: List[CorrectedPattern] = []

        for trace in traces:
            try:
                # Determine the correct route
                correct_route = None
                if correct_route_fn:
                    correct_route = correct_route_fn(trace.user_input)
                elif trace.feedback_comment:
                    # Try to extract route from feedback
                    correct_route = self._extract_route_from_feedback(trace.feedback_comment)

                if not correct_route:
                    logger.debug(f"Could not determine correct route for trace {trace.trace_id}")
                    continue

                # Generate variations using DeepEval
                variations = self._generate_variations(trace.user_input)

                # Generate golden answer
                golden_answer = self._generate_golden_answer(
                    trace.user_input,
                    correct_route,
                )

                # Create pattern
                pattern = CorrectedPattern(
                    query=trace.user_input.lower().strip(),
                    route=correct_route,
                    golden_answer=golden_answer,
                    variations=[v.lower().strip() for v in variations],
                    source_trace_id=trace.trace_id,
                    confidence=1.0,
                    created_at=datetime.utcnow().isoformat(),
                )

                patterns.append(pattern)

                # Also add patterns for variations
                for variation in variations:
                    var_pattern = CorrectedPattern(
                        query=variation.lower().strip(),
                        route=correct_route,
                        golden_answer=golden_answer,
                        variations=[],
                        source_trace_id=trace.trace_id,
                        confidence=0.9,  # Lower confidence for synthesized variations
                        created_at=datetime.utcnow().isoformat(),
                    )
                    patterns.append(var_pattern)

            except Exception as e:
                logger.warning(f"Error synthesizing correction for trace {trace.trace_id}: {e}")
                continue

        logger.info(f"Generated {len(patterns)} correction patterns")
        return patterns

    def _extract_route_from_feedback(self, comment: str) -> Optional[str]:
        """Try to extract correct route from feedback comment"""
        # Common patterns in feedback
        comment_lower = comment.lower()

        # Look for "should be X" or "correct: X" patterns
        patterns = [
            "should be ",
            "correct route: ",
            "expected: ",
            "should go to ",
        ]

        for pattern in patterns:
            if pattern in comment_lower:
                start = comment_lower.find(pattern) + len(pattern)
                # Extract word after pattern
                remaining = comment_lower[start:].strip()
                route = remaining.split()[0] if remaining.split() else None
                if route:
                    return route.strip(".,;:")

        return None

    def _generate_variations(self, query: str, num_variations: int = 3) -> List[str]:
        """Generate query variations using DeepEval synthesizer"""
        try:
            synthesizer = self._init_deepeval()

            # Use DeepEval's evolution methods to generate variations
            from deepeval.synthesizer.types import Evolution

            variations = []

            # Generate different types of variations
            evolution_types = [
                Evolution.PARAPHRASE,
                Evolution.SIMPLIFY,
                Evolution.CONTEXTUALIZE,
            ]

            for evolution in evolution_types[:num_variations]:
                try:
                    evolved = synthesizer.generate_goldens_from_docs(
                        docs=[query],
                        evolutions={evolution: 1.0}
                    )
                    if evolved:
                        for golden in evolved:
                            if hasattr(golden, 'input') and golden.input != query:
                                variations.append(golden.input)
                except Exception:
                    continue

            # Fallback: simple variations if DeepEval fails
            if len(variations) < num_variations:
                variations.extend(self._simple_variations(query, num_variations - len(variations)))

            return variations[:num_variations]

        except Exception as e:
            logger.warning(f"DeepEval synthesis failed, using fallback: {e}")
            return self._simple_variations(query, num_variations)

    def _simple_variations(self, query: str, num: int) -> List[str]:
        """Generate simple variations without DeepEval"""
        variations = []
        words = query.split()

        # Variation 1: Add "please"
        if "please" not in query.lower():
            variations.append(f"Please {query.lower()}")

        # Variation 2: Question form
        if not query.endswith("?"):
            variations.append(f"{query}?")

        # Variation 3: Rephrase with "help"
        if "help" not in query.lower():
            variations.append(f"Can you help me with {query.lower()}")

        return variations[:num]

    def _generate_golden_answer(self, query: str, route: str) -> str:
        """Generate a golden answer for the query"""
        # Simple template-based golden answer
        return f"This query should be routed to '{route}' for proper handling."

    def store_patterns(
        self,
        patterns: List[CorrectedPattern],
        output_path: str = "hot_fix_patterns.json",
        merge: bool = True,
    ) -> int:
        """
        Stage 3: Store corrected patterns to JSON file.

        Args:
            patterns: List of CorrectedPattern objects
            output_path: Path to output JSON file
            merge: If True, merge with existing patterns. If False, overwrite.

        Returns:
            Number of patterns stored
        """
        logger.info(f"Stage 3: Storing {len(patterns)} patterns to {output_path}...")

        output_file = Path(output_path)
        existing_patterns: List[Dict] = []

        # Load existing patterns if merging
        if merge and output_file.exists():
            try:
                with open(output_file, 'r') as f:
                    data = json.load(f)
                    existing_patterns = data.get("patterns", [])
            except Exception as e:
                logger.warning(f"Could not load existing patterns: {e}")

        # Create lookup for deduplication
        existing_queries = {p.get("query", ""): p for p in existing_patterns}

        # Merge new patterns
        for pattern in patterns:
            pattern_dict = pattern.to_dict()
            query_key = pattern_dict["query"]

            if query_key in existing_queries:
                # Update existing pattern if new one has higher confidence
                if pattern_dict["confidence"] > existing_queries[query_key].get("confidence", 0):
                    existing_queries[query_key] = pattern_dict
            else:
                existing_queries[query_key] = pattern_dict

        # Build output structure
        output_data = {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "pattern_count": len(existing_queries),
            "patterns": list(existing_queries.values()),
        }

        # Write to file
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Stored {len(existing_queries)} patterns to {output_path}")
            return len(existing_queries)
        except Exception as e:
            logger.error(f"Failed to write patterns: {e}")
            raise

    def run(
        self,
        output_path: str = "hot_fix_patterns.json",
        correct_route_fn: Optional[Callable[[str], str]] = None,
    ) -> PipelineResult:
        """
        Run the complete auto-fix pipeline.

        Args:
            output_path: Path to output JSON file
            correct_route_fn: Optional function to determine correct routes

        Returns:
            PipelineResult with run statistics
        """
        start_time = time.time()
        errors: List[str] = []

        logger.info("Starting Auto-Fix Pipeline...")

        # Stage 1: Fetch
        try:
            traces = self.fetch_negative_traces()
        except Exception as e:
            errors.append(f"Fetch error: {e}")
            traces = []

        # Stage 2: Synthesize
        try:
            patterns = self.synthesize_corrections(traces, correct_route_fn)
        except Exception as e:
            errors.append(f"Synthesis error: {e}")
            patterns = []

        # Stage 3: Store
        stored_count = 0
        try:
            if patterns:
                stored_count = self.store_patterns(patterns, output_path)
        except Exception as e:
            errors.append(f"Store error: {e}")

        duration = time.time() - start_time

        result = PipelineResult(
            traces_fetched=len(traces),
            patterns_generated=len(patterns),
            patterns_stored=stored_count,
            output_path=output_path,
            duration_seconds=duration,
            errors=errors,
        )

        logger.info(
            f"Pipeline complete: {result.traces_fetched} traces -> "
            f"{result.patterns_generated} patterns -> {result.patterns_stored} stored "
            f"({result.duration_seconds:.2f}s)"
        )

        return result

    def schedule(
        self,
        interval_hours: int = 24,
        output_path: str = "hot_fix_patterns.json",
        correct_route_fn: Optional[Callable[[str], str]] = None,
        max_runs: Optional[int] = None,
    ) -> None:
        """
        Schedule the pipeline to run periodically.

        Args:
            interval_hours: Hours between runs
            output_path: Path to output JSON file
            correct_route_fn: Optional function to determine correct routes
            max_runs: Maximum number of runs (None for infinite)
        """
        logger.info(f"Scheduling pipeline to run every {interval_hours} hours")

        run_count = 0
        while max_runs is None or run_count < max_runs:
            try:
                result = self.run(output_path, correct_route_fn)
                logger.info(f"Scheduled run {run_count + 1} complete: {result}")
            except Exception as e:
                logger.error(f"Scheduled run failed: {e}")

            run_count += 1
            if max_runs is None or run_count < max_runs:
                logger.info(f"Sleeping for {interval_hours} hours...")
                time.sleep(interval_hours * 3600)


# Convenience function for quick pipeline runs
def run_auto_fix(
    langfuse_public_key: str,
    langfuse_secret_key: str,
    output_path: str = "hot_fix_patterns.json",
    lookback_hours: int = 24,
) -> PipelineResult:
    """
    Quick function to run the auto-fix pipeline.

    Args:
        langfuse_public_key: Langfuse public API key
        langfuse_secret_key: Langfuse secret API key
        output_path: Path to output JSON file
        lookback_hours: How far back to look for traces

    Returns:
        PipelineResult with run statistics

    Example:
        from starvex._internals.auto_fix_pipeline import run_auto_fix

        result = run_auto_fix(
            langfuse_public_key="pk-lf-...",
            langfuse_secret_key="sk-lf-...",
            output_path="hot_fix_patterns.json",
        )
        print(f"Generated {result.patterns_generated} fix patterns")
    """
    pipeline = AutoFixPipeline(
        langfuse_public_key=langfuse_public_key,
        langfuse_secret_key=langfuse_secret_key,
        lookback_hours=lookback_hours,
    )
    return pipeline.run(output_path)


if __name__ == "__main__":
    import os

    # Run from environment variables
    pipeline = AutoFixPipeline(
        langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    )
    result = pipeline.run()
    print(f"Pipeline result: {result}")
