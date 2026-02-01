"""
FastAPI middleware for request ID tracking and resource cleanup.

This module provides middleware to:
1. Automatically handle X-Request-ID headers
2. Clean up resources (database sessions, Redis connections, etc.) after request completion
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from tomskit.server.context import set_request_id


logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle X-Request-ID header for request tracking.
    
    This middleware:
    1. Reads X-Request-ID from request headers (if present)
    2. Generates a new UUID if not present
    3. Sets the request ID to the context
    4. Adds X-Request-ID to response headers
    
    This enables distributed tracing and request correlation across services.
    
    Example:
        from tomskit.server import FastApp, RequestIDMiddleware
        
        app = FastApp()
        app.add_middleware(RequestIDMiddleware)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Request-ID",
        include_in_response: bool = True,
        generate_on_missing: bool = True,
    ):
        """
        Initialize RequestIDMiddleware.
        
        Args:
            app: The ASGI application.
            header_name: The header name to read/write request ID. Default: "X-Request-ID".
            include_in_response: Whether to include request ID in response headers. Default: True.
            generate_on_missing: Whether to generate a new ID if not present in request. Default: True.
        """
        super().__init__(app)
        self.header_name = header_name
        self.include_in_response = include_in_response
        self.generate_on_missing = generate_on_missing
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and set request ID in context.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.
            
        Returns:
            Response with X-Request-ID header (if enabled).
        """
        # 1. Try to get request ID from request headers
        request_id = request.headers.get(self.header_name)
        
        # 2. Generate new ID if not present and generation is enabled
        if not request_id and self.generate_on_missing:
            request_id = str(uuid.uuid4())
        
        # 3. Set request ID to context (if we have one)
        if request_id:
            set_request_id(request_id)
        
        # 4. Process the request
        response = await call_next(request)
        
        # 5. Add request ID to response headers (if enabled and we have one)
        if self.include_in_response and request_id:
            response.headers[self.header_name] = request_id
        
        return response


# ============================================================================
# Resource Cleanup Middleware (Strategy Pattern)
# ============================================================================

class CleanupStrategy(ABC):
    """
    Abstract base class for resource cleanup strategies.
    
    Defines a unified interface for resource cleanup, supporting multiple resource types
    (database, Redis, etc.). Each strategy is responsible for cleaning up a specific type of resource.
    """
    
    @abstractmethod
    async def cleanup(self, state: dict[str, Any]) -> None:
        """
        Execute resource cleanup.
        
        Args:
            state: ASGI scope state dictionary containing resource identifiers created during the request
        
        Raises:
            Exception: Any exceptions during cleanup should be caught and logged, not raised
        """
        pass
    
    @property
    @abstractmethod
    def resource_name(self) -> str:
        """
        Return resource name for logging purposes.
        
        Returns:
            Resource name string, e.g., "database_session" or "redis_client"
        """
        pass


class ResourceCleanupMiddleware:
    """
    Resource cleanup middleware.
    
    Uses strategy pattern to manage cleanup of multiple resources. Automatically cleans up
    resources created during the request (such as database sessions, Redis connections, etc.)
    after HTTP response completion to prevent resource leaks.
    
    How it works:
    1. Intercepts ASGI send calls using a message queue
    2. Listens for response completion event (http.response.body with more_body=False)
    3. Executes all registered cleanup strategies after response completion
    4. Ensures cleanup is executed even if application raises exceptions
    
    Features:
    - Supports cleanup of multiple resource types (via strategy pattern)
    - Automatic exception handling ensures cleanup logic doesn't affect responses
    - Supports streaming responses (Server-Sent Events, large file downloads, etc.)
    - Complete error handling and logging
    
    Example:
        from tomskit.server import FastApp, ResourceCleanupMiddleware
        from tomskit.sqlalchemy.database import DatabaseCleanupStrategy
        from tomskit.redis.redis_pool import RedisCleanupStrategy
        
        app = FastApp()
        
        # 使用数据库清理策略
        app.add_middleware(
            ResourceCleanupMiddleware,
            strategies=[DatabaseCleanupStrategy()]
        )
        
        # 或使用多个策略
        app.add_middleware(
            ResourceCleanupMiddleware,
            strategies=[
                DatabaseCleanupStrategy(),
                RedisCleanupStrategy(),
            ]
        )
        
        # If no strategies provided, no cleanup will be performed
        app.add_middleware(ResourceCleanupMiddleware)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        strategies: Optional[list[CleanupStrategy]] = None,
        cleanup_timeout: float = 5.0,
    ):
        """
        Initialize resource cleanup middleware.
        
        Args:
            app: ASGI application instance
            strategies: List of cleanup strategies. If None or empty, no cleanup will be performed
            cleanup_timeout: Timeout for cleanup operations in seconds, default 5.0
        """
        self.app = app
        self.cleanup_timeout = cleanup_timeout
        
        # If no strategies provided, use empty list (no cleanup will be performed)
        if strategies is None:
            self.strategies: list[CleanupStrategy] = []
        else:
            self.strategies = strategies
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle ASGI request.
        
        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Only handle HTTP requests
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        
        # If no cleanup strategies, skip the queue mechanism for efficiency
        if not self.strategies:
            await self.app(scope, receive, send)
            return
        
        # Get state (shared with request.state)
        # In Starlette, scope['state'] is a State object, not a dict
        # We should use it directly if it exists, otherwise create a dict
        if 'state' not in scope:
            scope['state'] = {}
        state = scope['state']
        
        # Create message queue to intercept send calls
        send_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        
        # Track if cleanup has been executed to avoid duplicate execution
        cleanup_executed = asyncio.Event()
        
        # Wrap send function to put messages into queue
        async def send_wrapper(message: dict[str, Any]) -> None:  # type: ignore
            await send_queue.put(message)
        
        # Sender coroutine: get messages from queue and send
        async def sender() -> None:
            """
            Sender coroutine responsible for getting messages from queue and sending to client.
            Triggers resource cleanup when response completion is detected.
            """
            response_completed = False
            try:
                while True:
                    message = await send_queue.get()
                    await send(message)
                    
                    # Detect response completion: http.response.body with more_body=False
                    if (
                        message['type'] == 'http.response.body' 
                        and not message.get('more_body', False)
                    ):
                        response_completed = True
                        break
                        
            except asyncio.CancelledError:
                # If cancelled, still attempt to cleanup resources
                response_completed = True
            except Exception as e:
                logger.error(f"Sender exception: {e}", exc_info=True)
                response_completed = True
            finally:
                # Execute resource cleanup regardless of normal completion
                if response_completed and not cleanup_executed.is_set():
                    cleanup_executed.set()
                    await self._execute_cleanup(state)
        
        # Application handler coroutine
        async def app_handler() -> None:
            """
            Application handler coroutine that executes actual request processing.
            """
            try:
                await self.app(scope, receive, send_wrapper)  # type: ignore[arg-type]
            except Exception as e:
                logger.error(f"Application handler exception: {e}", exc_info=True)
                # Even if application raises exception, ensure response completion signal is sent
                # so that sender can execute cleanup
                if send_queue.empty():
                    # If queue is empty, response has not been sent yet
                    # Send an error response to ensure cleanup execution
                    try:
                        await send_wrapper({
                            'type': 'http.response.start',
                            'status': 500,
                            'headers': [],
                        })
                        await send_wrapper({
                            'type': 'http.response.body',
                            'body': b'',
                            'more_body': False,
                        })
                    except Exception:
                        pass
                raise
        
        # Run application handler and sender concurrently
        # Use return_exceptions=True to prevent exceptions from stopping gather
        results = await asyncio.gather(
            app_handler(),
            sender(),
            return_exceptions=True,
        )
        
        # If cleanup hasn't been executed yet (e.g., app_handler failed before sending anything),
        # execute it now
        if not cleanup_executed.is_set():
            cleanup_executed.set()
            await self._execute_cleanup(state)
        
        # Re-raise exceptions from app_handler if any
        app_result = results[0]
        if isinstance(app_result, Exception):
            raise app_result
    
    async def _execute_cleanup(self, state: dict[str, Any]) -> None:
        """
        Execute all registered cleanup strategies.
        
        Args:
            state: ASGI scope state dictionary
        """
        if not self.strategies:
            return
        
        # Execute all cleanup strategies concurrently with timeout
        cleanup_tasks = [
            self._cleanup_with_timeout(strategy, state)
            for strategy in self.strategies
        ]
        
        results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # Check results and log
        for strategy, result in zip(self.strategies, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Cleanup strategy '{strategy.resource_name}' failed: {result}",
                    exc_info=result if isinstance(result, BaseException) else None,
                )
    
    async def _cleanup_with_timeout(
        self,
        strategy: CleanupStrategy,
        state: dict[str, Any],
    ) -> None:
        """
        Execute a single cleanup strategy with timeout protection.
        
        Args:
            strategy: Cleanup strategy instance
            state: ASGI scope state dictionary
        """
        try:
            await asyncio.wait_for(
                strategy.cleanup(state),
                timeout=self.cleanup_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"Cleanup strategy '{strategy.resource_name}' timed out "
                f"(timeout: {self.cleanup_timeout}s)"
            )
        except Exception as e:
            # Exceptions from cleanup strategies should not be raised
            logger.error(
                f"Cleanup strategy '{strategy.resource_name}' exception: {e}",
                exc_info=True,
            )
