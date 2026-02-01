"""
Message Bus Module

Provides inter-agent communication using publish-subscribe pattern.
Inspired by event-driven architectures for decoupled agent coordination.
"""

import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger


class MessageType(str, Enum):
    """Message types for inter-agent communication"""

    # Agent lifecycle events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    # Task-related events
    TASK_ASSIGNED = "task.assigned"
    TASK_PROGRESS = "task.progress"
    TASK_RESULT = "task.result"

    # Exploration events (Phase 1)
    EXPLORATION_STARTED = "exploration.started"
    EXPLORATION_FINDING = "exploration.finding"
    EXPLORATION_COMPLETED = "exploration.completed"

    # Planning events (Phase 2)
    PLAN_DRAFT = "plan.draft"
    PLAN_UPDATED = "plan.updated"
    PLAN_FINALIZED = "plan.finalized"

    # General events
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    CUSTOM = "custom"

    # Error events
    AGENT_ERROR = "agent.error"


@dataclass
class Message:
    """
    Message for inter-agent communication

    Attributes:
        topic: Message topic/channel
        message_type: Type of message
        sender_id: ID of the sending agent
        payload: Message content
        timestamp: When the message was created
        correlation_id: Optional ID to correlate request/response pairs
        metadata: Additional metadata
    """

    topic: str
    message_type: MessageType
    sender_id: str
    payload: Any
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "topic": self.topic,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


# Type aliases for callbacks
SyncCallback = Callable[[Message], None]
AsyncCallback = Callable[[Message], Coroutine[Any, Any, None]]
Callback = SyncCallback | AsyncCallback


class MessageBus:
    """
    Message Bus for inter-agent communication

    Features:
    - Publish-subscribe pattern
    - Topic-based filtering
    - Support for wildcard subscriptions (e.g., "agent.*")
    - Message history for replay
    - Async message delivery

    Example:
        >>> bus = MessageBus()
        >>>
        >>> # Subscribe to messages
        >>> async def on_finding(msg: Message):
        ...     print(f"Got finding: {msg.payload}")
        >>>
        >>> bus.subscribe("exploration.finding", on_finding)
        >>>
        >>> # Publish message
        >>> await bus.publish(Message(
        ...     topic="exploration.finding",
        ...     message_type=MessageType.EXPLORATION_FINDING,
        ...     sender_id="explore_001",
        ...     payload={"file": "src/main.py", "finding": "Entry point found"}
        ... ))
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize message bus

        Args:
            max_history: Maximum number of messages to keep in history
        """
        self._subscribers: dict[str, list[Callback]] = defaultdict(list)
        self._history: list[Message] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()

    def subscribe(self, topic: str, callback: Callback) -> None:
        """
        Subscribe to messages on a topic

        Args:
            topic: Topic to subscribe to (supports wildcards like "agent.*")
            callback: Function to call when message is received
                      Can be sync or async function

        Example:
            >>> def handle_message(msg):
            ...     print(f"Received: {msg.payload}")
            >>>
            >>> bus.subscribe("task.result", handle_message)
        """
        self._subscribers[topic].append(callback)
        logger.debug(f"Subscribed to topic: {topic}")

    def unsubscribe(self, topic: str, callback: Callback) -> bool:
        """
        Unsubscribe from a topic

        Args:
            topic: Topic to unsubscribe from
            callback: The callback function to remove

        Returns:
            True if callback was found and removed, False otherwise
        """
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(callback)
                logger.debug(f"Unsubscribed from topic: {topic}")
                return True
            except ValueError:
                return False
        return False

    async def publish(self, message: Message) -> int:
        """
        Publish a message to all subscribers

        Args:
            message: Message to publish

        Returns:
            Number of subscribers that received the message

        Example:
            >>> await bus.publish(Message(
            ...     topic="agent.started",
            ...     message_type=MessageType.AGENT_STARTED,
            ...     sender_id="explore_001",
            ...     payload={"task": "Find Python files"}
            ... ))
        """
        async with self._lock:
            # Add to history
            self._history.append(message)
            if len(self._history) > self._max_history:
                self._history.pop(0)

        # Find matching subscribers
        matching_callbacks = self._find_matching_callbacks(message.topic)

        logger.debug(
            f"Publishing message: topic={message.topic}, "
            f"type={message.message_type.value}, "
            f"subscribers={len(matching_callbacks)}"
        )

        # Deliver to all matching subscribers
        delivery_count = 0
        for callback in matching_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
                delivery_count += 1
            except Exception as e:
                logger.error(f"Error delivering message to subscriber: {e}")

        return delivery_count

    def _find_matching_callbacks(self, topic: str) -> list[Callback]:
        """
        Find all callbacks that match a topic

        Supports wildcard matching:
        - "agent.*" matches "agent.started", "agent.completed", etc.
        - "*" matches all topics

        Args:
            topic: Topic to match

        Returns:
            List of matching callbacks
        """
        matching: list[Callback] = []

        for pattern, callbacks in self._subscribers.items():
            if self._topic_matches(pattern, topic):
                matching.extend(callbacks)

        return matching

    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """
        Check if a topic matches a pattern

        Args:
            pattern: Pattern with optional wildcards
            topic: Actual topic

        Returns:
            True if topic matches pattern
        """
        # Exact match
        if pattern == topic:
            return True

        # Wildcard match all
        if pattern == "*":
            return True

        # Prefix wildcard match (e.g., "agent.*" matches "agent.started")
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return topic.startswith(prefix + ".")

        return False

    def get_history(
        self,
        topic: str | None = None,
        sender_id: str | None = None,
        message_type: MessageType | None = None,
        limit: int | None = None,
    ) -> list[Message]:
        """
        Get message history with optional filtering

        Args:
            topic: Filter by topic (optional)
            sender_id: Filter by sender (optional)
            message_type: Filter by message type (optional)
            limit: Maximum number of messages to return (optional)

        Returns:
            List of messages matching the filters
        """
        results = self._history.copy()

        # Apply filters
        if topic:
            results = [m for m in results if self._topic_matches(topic, m.topic)]
        if sender_id:
            results = [m for m in results if m.sender_id == sender_id]
        if message_type:
            results = [m for m in results if m.message_type == message_type]

        # Apply limit
        if limit:
            results = results[-limit:]

        return results

    def clear_history(self) -> int:
        """
        Clear message history

        Returns:
            Number of messages cleared
        """
        count = len(self._history)
        self._history.clear()
        logger.debug(f"Cleared {count} messages from history")
        return count

    def get_subscriber_count(self, topic: str | None = None) -> int:
        """
        Get number of subscribers

        Args:
            topic: Count subscribers for specific topic (optional)

        Returns:
            Number of subscribers
        """
        if topic:
            return len(self._subscribers.get(topic, []))
        return sum(len(callbacks) for callbacks in self._subscribers.values())

    def list_topics(self) -> list[str]:
        """
        List all topics with active subscribers

        Returns:
            List of topic names
        """
        return list(self._subscribers.keys())

    async def request_response(
        self,
        request: Message,
        response_topic: str,
        timeout: float = 30.0,
    ) -> Message | None:
        """
        Send a request and wait for a response

        Args:
            request: Request message to send
            response_topic: Topic to listen for response
            timeout: Maximum time to wait for response in seconds

        Returns:
            Response message or None if timeout

        Example:
            >>> response = await bus.request_response(
            ...     request=Message(
            ...         topic="agent.request",
            ...         message_type=MessageType.REQUEST,
            ...         sender_id="main",
            ...         payload={"action": "get_status"},
            ...         correlation_id="req_001"
            ...     ),
            ...     response_topic="agent.response",
            ...     timeout=5.0
            ... )
        """
        response_received = asyncio.Event()
        response_message: list[Message] = []  # Use list to capture in closure

        async def response_handler(msg: Message):
            if msg.correlation_id == request.correlation_id:
                response_message.append(msg)
                response_received.set()

        # Subscribe to response topic
        self.subscribe(response_topic, response_handler)

        try:
            # Publish request
            await self.publish(request)

            # Wait for response
            try:
                await asyncio.wait_for(response_received.wait(), timeout=timeout)
                return response_message[0] if response_message else None
            except TimeoutError:
                logger.warning(f"Request-response timeout: correlation_id={request.correlation_id}")
                return None
        finally:
            # Unsubscribe from response topic
            self.unsubscribe(response_topic, response_handler)

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"MessageBus(topics={len(self._subscribers)}, "
            f"subscribers={self.get_subscriber_count()}, "
            f"history={len(self._history)})"
        )
