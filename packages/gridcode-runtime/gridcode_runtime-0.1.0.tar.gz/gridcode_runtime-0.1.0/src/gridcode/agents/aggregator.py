"""
Result Aggregator Module

Aggregates results from multiple agents using various strategies.
Supports merging, prioritization, and voting-based aggregation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus, AgentType


class AggregationStrategy(str, Enum):
    """Strategies for aggregating multiple agent results"""

    MERGE = "merge"  # Combine all results into one
    FIRST_SUCCESS = "first_success"  # Return first successful result
    PRIORITY = "priority"  # Return result from highest priority agent
    VOTE = "vote"  # Use voting for consensus (for boolean/categorical results)
    BEST_SCORE = "best_score"  # Return result with highest score


@dataclass
class AggregatedResult:
    """
    Result of aggregating multiple agent results

    Attributes:
        strategy: Strategy used for aggregation
        source_results: Original results that were aggregated
        output: Aggregated output
        metadata: Aggregation metadata
        success: Whether aggregation was successful
        error: Error message if aggregation failed
    """

    strategy: AggregationStrategy
    source_results: list[AgentResult]
    output: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None

    @property
    def source_count(self) -> int:
        """Number of source results"""
        return len(self.source_results)

    @property
    def success_count(self) -> int:
        """Number of successful source results"""
        return sum(1 for r in self.source_results if r.status == AgentStatus.COMPLETED)

    @property
    def failure_count(self) -> int:
        """Number of failed source results"""
        return sum(1 for r in self.source_results if r.status == AgentStatus.FAILED)


class BaseAggregator(ABC):
    """Abstract base class for result aggregators"""

    @abstractmethod
    def aggregate(self, results: list[AgentResult]) -> AggregatedResult:
        """
        Aggregate multiple agent results

        Args:
            results: List of agent results to aggregate

        Returns:
            Aggregated result
        """
        pass


class MergeAggregator(BaseAggregator):
    """
    Merge aggregator - combines all results into one

    Useful for exploration results where each agent finds different information.
    """

    def __init__(self, separator: str = "\n\n---\n\n"):
        """
        Initialize merge aggregator

        Args:
            separator: String to use between merged outputs
        """
        self.separator = separator

    def aggregate(self, results: list[AgentResult]) -> AggregatedResult:
        """Merge all results into one combined output"""
        if not results:
            return AggregatedResult(
                strategy=AggregationStrategy.MERGE,
                source_results=[],
                output="",
                success=False,
                error="No results to aggregate",
            )

        # Filter successful results
        successful = [r for r in results if r.status == AgentStatus.COMPLETED]

        if not successful:
            return AggregatedResult(
                strategy=AggregationStrategy.MERGE,
                source_results=results,
                output="",
                success=False,
                error="All agent results failed",
            )

        # Merge outputs
        merged_parts = []
        for result in successful:
            header = f"## Result from {result.agent_type.value} ({result.agent_id})"
            merged_parts.append(f"{header}\n\n{result.output}")

        merged_output = self.separator.join(merged_parts)

        return AggregatedResult(
            strategy=AggregationStrategy.MERGE,
            source_results=results,
            output=merged_output,
            metadata={
                "merged_count": len(successful),
                "total_count": len(results),
                "agent_types": [r.agent_type.value for r in successful],
            },
        )


class FirstSuccessAggregator(BaseAggregator):
    """
    First success aggregator - returns first successful result

    Useful when any successful result is acceptable.
    """

    def aggregate(self, results: list[AgentResult]) -> AggregatedResult:
        """Return first successful result"""
        if not results:
            return AggregatedResult(
                strategy=AggregationStrategy.FIRST_SUCCESS,
                source_results=[],
                output=None,
                success=False,
                error="No results to aggregate",
            )

        # Find first successful result
        for result in results:
            if result.status == AgentStatus.COMPLETED:
                return AggregatedResult(
                    strategy=AggregationStrategy.FIRST_SUCCESS,
                    source_results=results,
                    output=result.output,
                    metadata={
                        "selected_agent_id": result.agent_id,
                        "selected_agent_type": result.agent_type.value,
                        "position": results.index(result),
                    },
                )

        return AggregatedResult(
            strategy=AggregationStrategy.FIRST_SUCCESS,
            source_results=results,
            output=None,
            success=False,
            error="No successful results found",
        )


class PriorityAggregator(BaseAggregator):
    """
    Priority aggregator - returns result from highest priority agent type

    Useful when certain agent types are more authoritative.
    """

    # Default priority order (higher index = higher priority)
    DEFAULT_PRIORITY = {
        AgentType.EXPLORE: 1,
        AgentType.PLAN: 2,
        AgentType.CODE_REVIEW: 3,
        AgentType.TEST_RUNNER: 2,
        AgentType.MAIN: 4,
    }

    def __init__(self, priority_map: dict[AgentType, int] | None = None):
        """
        Initialize priority aggregator

        Args:
            priority_map: Custom priority mapping (higher = more priority)
        """
        self.priority_map = priority_map or self.DEFAULT_PRIORITY

    def aggregate(self, results: list[AgentResult]) -> AggregatedResult:
        """Return result from highest priority agent"""
        if not results:
            return AggregatedResult(
                strategy=AggregationStrategy.PRIORITY,
                source_results=[],
                output=None,
                success=False,
                error="No results to aggregate",
            )

        # Filter successful results
        successful = [r for r in results if r.status == AgentStatus.COMPLETED]

        if not successful:
            return AggregatedResult(
                strategy=AggregationStrategy.PRIORITY,
                source_results=results,
                output=None,
                success=False,
                error="No successful results found",
            )

        # Sort by priority (descending)
        sorted_results = sorted(
            successful,
            key=lambda r: self.priority_map.get(r.agent_type, 0),
            reverse=True,
        )

        selected = sorted_results[0]

        return AggregatedResult(
            strategy=AggregationStrategy.PRIORITY,
            source_results=results,
            output=selected.output,
            metadata={
                "selected_agent_id": selected.agent_id,
                "selected_agent_type": selected.agent_type.value,
                "priority": self.priority_map.get(selected.agent_type, 0),
            },
        )


class BestScoreAggregator(BaseAggregator):
    """
    Best score aggregator - returns result with highest score

    Useful when results have quality scores in metadata.
    """

    def __init__(self, score_key: str = "score"):
        """
        Initialize best score aggregator

        Args:
            score_key: Key in result metadata containing the score
        """
        self.score_key = score_key

    def aggregate(self, results: list[AgentResult]) -> AggregatedResult:
        """Return result with highest score"""
        if not results:
            return AggregatedResult(
                strategy=AggregationStrategy.BEST_SCORE,
                source_results=[],
                output=None,
                success=False,
                error="No results to aggregate",
            )

        # Filter successful results with scores
        scored = [
            r for r in results if r.status == AgentStatus.COMPLETED and self.score_key in r.metadata
        ]

        if not scored:
            # Fall back to first successful
            successful = [r for r in results if r.status == AgentStatus.COMPLETED]
            if successful:
                return AggregatedResult(
                    strategy=AggregationStrategy.BEST_SCORE,
                    source_results=results,
                    output=successful[0].output,
                    metadata={
                        "selected_agent_id": successful[0].agent_id,
                        "fallback": True,
                        "reason": "No scored results, using first successful",
                    },
                )
            return AggregatedResult(
                strategy=AggregationStrategy.BEST_SCORE,
                source_results=results,
                output=None,
                success=False,
                error="No successful results found",
            )

        # Find best score
        best = max(scored, key=lambda r: r.metadata.get(self.score_key, 0))

        return AggregatedResult(
            strategy=AggregationStrategy.BEST_SCORE,
            source_results=results,
            output=best.output,
            metadata={
                "selected_agent_id": best.agent_id,
                "selected_agent_type": best.agent_type.value,
                "score": best.metadata.get(self.score_key),
                "score_key": self.score_key,
            },
        )


class ResultAggregator:
    """
    Main result aggregator with strategy selection

    Example:
        >>> aggregator = ResultAggregator()
        >>>
        >>> # Merge exploration results
        >>> merged = aggregator.aggregate(
        ...     results=explore_results,
        ...     strategy=AggregationStrategy.MERGE
        ... )
        >>>
        >>> # Get best plan from multiple perspectives
        >>> best_plan = aggregator.aggregate(
        ...     results=plan_results,
        ...     strategy=AggregationStrategy.BEST_SCORE,
        ...     score_key="confidence"
        ... )
    """

    def __init__(self):
        """Initialize result aggregator"""
        self._aggregators: dict[AggregationStrategy, BaseAggregator] = {
            AggregationStrategy.MERGE: MergeAggregator(),
            AggregationStrategy.FIRST_SUCCESS: FirstSuccessAggregator(),
            AggregationStrategy.PRIORITY: PriorityAggregator(),
            AggregationStrategy.BEST_SCORE: BestScoreAggregator(),
        }

    def aggregate(
        self,
        results: list[AgentResult],
        strategy: AggregationStrategy = AggregationStrategy.MERGE,
        **kwargs,
    ) -> AggregatedResult:
        """
        Aggregate results using specified strategy

        Args:
            results: List of agent results to aggregate
            strategy: Aggregation strategy to use
            **kwargs: Additional arguments for specific strategies:
                - separator: For MERGE strategy
                - priority_map: For PRIORITY strategy
                - score_key: For BEST_SCORE strategy

        Returns:
            Aggregated result
        """
        logger.debug(f"Aggregating {len(results)} results using {strategy.value} strategy")

        # Get or create aggregator with custom config
        aggregator = self._get_aggregator(strategy, **kwargs)

        try:
            result = aggregator.aggregate(results)
            logger.debug(
                f"Aggregation complete: success={result.success}, "
                f"source_count={result.source_count}"
            )
            return result
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return AggregatedResult(
                strategy=strategy,
                source_results=results,
                output=None,
                success=False,
                error=str(e),
            )

    def _get_aggregator(
        self,
        strategy: AggregationStrategy,
        **kwargs,
    ) -> BaseAggregator:
        """
        Get aggregator for strategy, optionally with custom config

        Args:
            strategy: Aggregation strategy
            **kwargs: Custom configuration

        Returns:
            Aggregator instance
        """
        if strategy == AggregationStrategy.MERGE and "separator" in kwargs:
            return MergeAggregator(separator=kwargs["separator"])
        elif strategy == AggregationStrategy.PRIORITY and "priority_map" in kwargs:
            return PriorityAggregator(priority_map=kwargs["priority_map"])
        elif strategy == AggregationStrategy.BEST_SCORE and "score_key" in kwargs:
            return BestScoreAggregator(score_key=kwargs["score_key"])

        return self._aggregators[strategy]

    def register_aggregator(
        self,
        strategy: AggregationStrategy,
        aggregator: BaseAggregator,
    ) -> None:
        """
        Register a custom aggregator for a strategy

        Args:
            strategy: Strategy to register for
            aggregator: Aggregator instance
        """
        self._aggregators[strategy] = aggregator
        logger.debug(f"Registered custom aggregator for {strategy.value}")

    def __repr__(self) -> str:
        """String representation"""
        return f"ResultAggregator(strategies={list(self._aggregators.keys())})"
