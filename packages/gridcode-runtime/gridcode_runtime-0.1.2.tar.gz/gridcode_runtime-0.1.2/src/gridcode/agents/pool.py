"""
Agent Pool Module

Manages agent lifecycle, parallel execution, and result aggregation.
Inspired by Claude Code's agent spawning and management system.

Note: This module uses lazy loading for agent classes to improve startup time.
Agent classes are imported only when first needed for instantiation.
"""

import asyncio
import hashlib
import time
from typing import TYPE_CHECKING, Any

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus, AgentType, BaseAgent
from gridcode.core.context import ExecutionContext

# Type checking imports - these won't be executed at runtime
if TYPE_CHECKING:
    pass


class CacheEntry:
    """Single cache entry with timestamp"""

    __slots__ = ("result", "timestamp", "access_count")

    def __init__(self, result: AgentResult):
        self.result = result
        self.timestamp = time.time()
        self.access_count = 1

    def touch(self) -> None:
        """Update access count and timestamp for LRU tracking"""
        self.access_count += 1


class AgentResultCache:
    """
    Agent result cache with TTL and LRU eviction.

    Caches agent execution results to avoid redundant executions
    for identical tasks. Uses SHA-256 hash of task parameters as cache key.

    Features:
    - TTL-based expiration (default 1 hour)
    - LRU eviction when max size reached
    - Size limit for cached results (skip large results)
    - Cache statistics tracking

    Example:
        >>> cache = AgentResultCache(max_size=100, ttl=3600.0)
        >>> key = cache.generate_key("explore", "Find Python files", thoroughness="medium")
        >>> cache.set(key, result)
        >>> cached = cache.get(key)
    """

    # Maximum size of result to cache (1MB in bytes, estimated from JSON)
    MAX_RESULT_SIZE = 1024 * 1024

    def __init__(
        self,
        max_size: int = 100,
        ttl: float = 3600.0,
        enabled: bool = True,
    ):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cached entries (default 100)
            ttl: Time-to-live in seconds (default 3600 = 1 hour)
            enabled: Whether caching is enabled (default True)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.enabled = enabled
        self._cache: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._size_skips = 0

    def generate_key(self, agent_type: str, task: str, **kwargs) -> str:
        """
        Generate cache key from task parameters.

        Args:
            agent_type: Type of agent (e.g., "explore", "plan")
            task: Task description
            **kwargs: Additional parameters (thoroughness, etc.)

        Returns:
            SHA-256 hash string as cache key
        """
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        # Create content string for hashing
        content = f"{agent_type}:{task}:{sorted_kwargs}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, key: str) -> AgentResult | None:
        """
        Get cached result if valid.

        Args:
            key: Cache key

        Returns:
            Cached AgentResult if valid, None otherwise
        """
        if not self.enabled:
            self._misses += 1
            return None

        if key in self._cache:
            entry = self._cache[key]
            # Check TTL
            if time.time() - entry.timestamp < self.ttl:
                self._hits += 1
                entry.touch()
                logger.debug(f"Cache hit for key: {key[:16]}...")
                return entry.result
            else:
                # Expired, remove entry
                del self._cache[key]
                logger.debug(f"Cache expired for key: {key[:16]}...")

        self._misses += 1
        return None

    def set(self, key: str, result: AgentResult) -> bool:
        """
        Cache result with TTL.

        Args:
            key: Cache key
            result: AgentResult to cache

        Returns:
            True if cached successfully, False if skipped (size limit)
        """
        if not self.enabled:
            return False

        # Check result size (estimate from JSON serialization)
        try:
            result_size = len(result.model_dump_json())
            if result_size > self.MAX_RESULT_SIZE:
                self._size_skips += 1
                logger.debug(f"Skipping cache for large result ({result_size} bytes)")
                return False
        except Exception:
            # If we can't serialize, skip caching
            self._size_skips += 1
            return False

        # LRU eviction if full
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        self._cache[key] = CacheEntry(result)
        logger.debug(f"Cached result for key: {key[:16]}...")
        return True

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self._cache:
            return

        # Find entry with oldest timestamp (considering access count)
        # LRU: prioritize removing entries with low access count and old timestamp
        def lru_score(item: tuple[str, CacheEntry]) -> float:
            _, entry = item
            age = time.time() - entry.timestamp
            # Higher score = more likely to evict
            return age / (entry.access_count + 1)

        oldest_key = max(self._cache.items(), key=lru_score)[0]
        del self._cache[oldest_key]
        self._evictions += 1
        logger.debug(f"Evicted LRU entry: {oldest_key[:16]}...")

    def clear(self) -> int:
        """
        Clear all cached entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cached entries")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() if now - entry.timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "enabled": self.enabled,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "evictions": self._evictions,
            "size_skips": self._size_skips,
        }

    def __repr__(self) -> str:
        """String representation"""
        stats = self.get_stats()
        return (
            f"AgentResultCache(size={stats['size']}/{stats['max_size']}, "
            f"hit_rate={stats['hit_rate']:.1%}, enabled={self.enabled})"
        )


class AgentFactory:
    """
    Factory for creating agent instances

    Supports creating different types of agents based on AgentType enum.
    """

    @staticmethod
    def create_agent(agent_type: AgentType, agent_id: str | None = None) -> BaseAgent:
        """
        Create agent instance by type

        Args:
            agent_type: Type of agent to create
            agent_id: Optional custom agent ID

        Returns:
            Agent instance

        Raises:
            ValueError: If agent type is not supported
        """
        # Core agents - imported on-demand
        if agent_type == AgentType.EXPLORE:
            from gridcode.agents.explore import ExploreAgent

            return ExploreAgent(agent_id=agent_id)
        elif agent_type == AgentType.PLAN:
            from gridcode.agents.plan import PlanAgent

            return PlanAgent(agent_id=agent_id)
        elif agent_type == AgentType.CODE_REVIEW:
            from gridcode.agents.review import ReviewAgent

            return ReviewAgent(agent_id=agent_id)
        elif agent_type == AgentType.TEST_RUNNER:
            from gridcode.agents.test_runner import TestRunnerAgent

            return TestRunnerAgent(agent_id=agent_id)
        # Expert agents - imported on-demand
        elif agent_type == AgentType.CODE_REVIEWER:
            from gridcode.agents.experts import CodeReviewerAgent

            return CodeReviewerAgent(agent_id=agent_id)
        elif agent_type == AgentType.DEBUGGER:
            from gridcode.agents.experts import DebuggerAgent

            return DebuggerAgent(agent_id=agent_id)
        elif agent_type == AgentType.ARCHITECT:
            from gridcode.agents.experts import ArchitectAgent

            return ArchitectAgent(agent_id=agent_id)
        # Documentation agents - imported on-demand
        elif agent_type == AgentType.DOCS_ARCHITECT:
            from gridcode.agents.documentation import DocsArchitectAgent

            return DocsArchitectAgent(agent_id=agent_id)
        elif agent_type == AgentType.TUTORIAL_ENGINEER:
            from gridcode.agents.documentation import TutorialEngineerAgent

            return TutorialEngineerAgent(agent_id=agent_id)
        elif agent_type == AgentType.API_DOCUMENTER:
            from gridcode.agents.documentation import APIDocumenterAgent

            return APIDocumenterAgent(agent_id=agent_id)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")


class AgentPool:
    """
    Agent Pool Manager

    Manages agent lifecycle, parallel execution, and result collection.
    Inspired by Claude Code's Task tool and agent spawning system.

    Features:
    - Spawn single or multiple agents
    - Parallel agent execution
    - Wait for agent completion
    - Terminate running agents
    - Track agent status
    - Result caching with TTL and LRU eviction

    Example:
        >>> pool = AgentPool()
        >>> agent_id = await pool.spawn_agent(
        ...     agent_type=AgentType.EXPLORE,
        ...     task="Find all Python files",
        ...     context=context
        ... )
        >>> result = await pool.wait_for_agent(agent_id)

        # With caching enabled (default)
        >>> pool = AgentPool(cache_enabled=True)
        >>> stats = pool.get_cache_stats()
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        cache_max_size: int = 100,
        cache_ttl: float = 3600.0,
    ):
        """
        Initialize agent pool.

        Args:
            cache_enabled: Enable result caching (default True)
            cache_max_size: Maximum cached entries (default 100)
            cache_ttl: Cache TTL in seconds (default 3600 = 1 hour)
        """
        self._agents: dict[str, BaseAgent] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._results: dict[str, AgentResult] = {}
        self._cache = AgentResultCache(
            max_size=cache_max_size,
            ttl=cache_ttl,
            enabled=cache_enabled,
        )

    async def spawn_agent(
        self,
        agent_type: AgentType,
        task: str,
        context: ExecutionContext,
        agent_id: str | None = None,
        use_cache: bool = True,
        **kwargs,
    ) -> str:
        """
        Spawn a single agent

        Args:
            agent_type: Type of agent to spawn
            task: Task description for the agent
            context: Execution context
            agent_id: Optional custom agent ID
            use_cache: Whether to use cached result if available (default True)
            **kwargs: Additional arguments passed to agent.execute()

        Returns:
            Agent ID for tracking

        Example:
            >>> agent_id = await pool.spawn_agent(
            ...     agent_type=AgentType.EXPLORE,
            ...     task="Find configuration files",
            ...     context=context,
            ...     thoroughness="medium"
            ... )
        """
        # Check cache first (if enabled and requested)
        cache_key = None
        if use_cache and self._cache.enabled:
            cache_key = self._cache.generate_key(agent_type.value, task, **kwargs)
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                # Create a synthetic agent ID for cached result
                agent = AgentFactory.create_agent(agent_type, agent_id)
                synthetic_id = f"cached_{agent.agent_id}"

                logger.info(
                    f"Using cached result for agent: {synthetic_id} (type={agent_type.value})"
                )

                # Store cached result with synthetic ID
                self._agents[synthetic_id] = agent
                self._results[synthetic_id] = cached_result

                # Create a completed task placeholder
                async def noop():
                    return cached_result

                completed_task = asyncio.create_task(noop())
                self._tasks[synthetic_id] = completed_task

                return synthetic_id

        # Create agent
        agent = AgentFactory.create_agent(agent_type, agent_id)
        agent_id = agent.agent_id

        logger.info(f"Spawning agent: {agent_id} (type={agent_type.value})")

        # Store agent
        self._agents[agent_id] = agent

        # Create async task
        async_task = asyncio.create_task(agent.execute(task, context, **kwargs))
        self._tasks[agent_id] = async_task

        # Store result when task completes (with caching)
        async_task.add_done_callback(
            lambda t: self._on_task_complete(agent_id, t, cache_key=cache_key)
        )

        return agent_id

    async def spawn_parallel_agents(
        self,
        agent_configs: list[dict[str, Any]],
    ) -> list[str]:
        """
        Spawn multiple agents in parallel

        Args:
            agent_configs: List of agent configurations, each containing:
                - agent_type: AgentType
                - task: str
                - context: ExecutionContext
                - agent_id: str (optional)
                - **kwargs: Additional arguments

        Returns:
            List of agent IDs

        Example:
            >>> agent_ids = await pool.spawn_parallel_agents([
            ...     {
            ...         "agent_type": AgentType.EXPLORE,
            ...         "task": "Find Python files",
            ...         "context": context,
            ...     },
            ...     {
            ...         "agent_type": AgentType.EXPLORE,
            ...         "task": "Find JavaScript files",
            ...         "context": context,
            ...     },
            ... ])
        """
        logger.info(f"Spawning {len(agent_configs)} agents in parallel")

        # Spawn all agents concurrently
        agent_ids = await asyncio.gather(*[self.spawn_agent(**config) for config in agent_configs])

        return list(agent_ids)

    async def wait_for_agent(self, agent_id: str, timeout: float | None = None) -> AgentResult:
        """
        Wait for a specific agent to complete

        Args:
            agent_id: Agent ID to wait for
            timeout: Optional timeout in seconds

        Returns:
            AgentResult when agent completes

        Raises:
            KeyError: If agent ID not found
            TimeoutError: If timeout exceeded
        """
        if agent_id not in self._tasks:
            raise KeyError(f"Agent not found: {agent_id}")

        logger.debug(f"Waiting for agent: {agent_id}")

        try:
            if timeout:
                await asyncio.wait_for(self._tasks[agent_id], timeout=timeout)
            else:
                await self._tasks[agent_id]

            return self._results[agent_id]

        except TimeoutError:
            logger.error(f"Agent {agent_id} timed out after {timeout}s")
            self.terminate_agent(agent_id)
            raise

    async def wait_for_all(
        self,
        agent_ids: list[str],
        timeout: float | None = None,
    ) -> list[AgentResult]:
        """
        Wait for multiple agents to complete

        Args:
            agent_ids: List of agent IDs to wait for
            timeout: Optional timeout in seconds (applies to all agents)

        Returns:
            List of AgentResults in the same order as agent_ids

        Raises:
            KeyError: If any agent ID not found
            TimeoutError: If timeout exceeded
        """
        logger.info(f"Waiting for {len(agent_ids)} agents to complete")

        # Wait for all agents
        results = await asyncio.gather(
            *[self.wait_for_agent(agent_id, timeout) for agent_id in agent_ids]
        )

        return results

    def terminate_agent(self, agent_id: str) -> None:
        """
        Terminate a running agent

        Args:
            agent_id: Agent ID to terminate

        Raises:
            KeyError: If agent ID not found
        """
        if agent_id not in self._tasks:
            raise KeyError(f"Agent not found: {agent_id}")

        logger.warning(f"Terminating agent: {agent_id}")

        task = self._tasks[agent_id]
        if not task.done():
            task.cancel()

    def get_agent_status(self, agent_id: str) -> AgentStatus:
        """
        Get current status of an agent

        Args:
            agent_id: Agent ID to check

        Returns:
            AgentStatus

        Raises:
            KeyError: If agent ID not found
        """
        if agent_id not in self._agents:
            raise KeyError(f"Agent not found: {agent_id}")

        # Check if result is available
        if agent_id in self._results:
            return self._results[agent_id].status

        # Check if task is running
        if agent_id in self._tasks:
            task = self._tasks[agent_id]
            if task.done():
                return AgentStatus.COMPLETED
            else:
                return AgentStatus.RUNNING

        return AgentStatus.IDLE

    def get_agent(self, agent_id: str) -> BaseAgent:
        """
        Get agent instance by ID

        Args:
            agent_id: Agent ID

        Returns:
            Agent instance

        Raises:
            KeyError: If agent ID not found
        """
        if agent_id not in self._agents:
            raise KeyError(f"Agent not found: {agent_id}")

        return self._agents[agent_id]

    def get_result(self, agent_id: str) -> AgentResult | None:
        """
        Get agent result if available

        Args:
            agent_id: Agent ID

        Returns:
            AgentResult if available, None otherwise
        """
        return self._results.get(agent_id)

    def list_agents(self) -> list[str]:
        """
        List all agent IDs in the pool

        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())

    def _on_task_complete(
        self, agent_id: str, task: asyncio.Task, cache_key: str | None = None
    ) -> None:
        """
        Callback when agent task completes

        Args:
            agent_id: Agent ID
            task: Completed asyncio task
            cache_key: Optional cache key to store result
        """
        try:
            result = task.result()
            self._results[agent_id] = result
            logger.info(f"Agent {agent_id} completed with status: {result.status.value}")

            # Cache successful results
            if cache_key and result.status == AgentStatus.COMPLETED:
                self._cache.set(cache_key, result)

        except Exception as e:
            logger.error(f"Agent {agent_id} failed with exception: {e}")
            # Create failed result
            agent = self._agents[agent_id]
            result = AgentResult(
                agent_id=agent_id,
                agent_type=agent.agent_type,
                status=AgentStatus.FAILED,
                error=str(e),
            )
            self._results[agent_id] = result

    # ========== Cache Management ==========

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics including:
            - enabled: Whether caching is enabled
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate: Cache hit rate (0.0 - 1.0)
            - size: Current number of cached entries
            - max_size: Maximum cache size
            - ttl: Time-to-live in seconds
            - evictions: Number of LRU evictions
            - size_skips: Number of large results skipped
        """
        return self._cache.get_stats()

    def clear_cache(self) -> int:
        """
        Clear all cached results.

        Returns:
            Number of entries cleared
        """
        return self._cache.clear()

    def cleanup_cache(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        return self._cache.cleanup_expired()

    def set_cache_enabled(self, enabled: bool) -> None:
        """
        Enable or disable caching.

        Args:
            enabled: Whether to enable caching
        """
        self._cache.enabled = enabled
        logger.info(f"Cache {'enabled' if enabled else 'disabled'}")

    def __repr__(self) -> str:
        """String representation of agent pool"""
        cache_stats = self._cache.get_stats()
        return (
            f"AgentPool(agents={len(self._agents)}, "
            f"running={sum(1 for t in self._tasks.values() if not t.done())}, "
            f"completed={len(self._results)}, "
            f"cache_size={cache_stats['size']}, "
            f"cache_hit_rate={cache_stats['hit_rate']:.1%})"
        )
