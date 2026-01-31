"""Low-level API client for Glaium Optimizer."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from glaium.auth import get_api_key, get_base_url
from glaium.exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    ReasoningError,
    ReasoningTimeoutError,
    ServerError,
    TimeoutError,
    ValidationError,
    VerificationError,
)
from glaium.models import (
    AgentConnection,
    AgentInput,
    AgentOutput,
    Event,
    EventResponse,
    HandsUpFeedbackResponse,
    Optimization,
    RegistrationResponse,
)
from glaium.retry import RetryConfig, retry_async, retry_sync


class Client:
    """
    Low-level client for the Glaium Optimizer API.

    Provides direct access to all API endpoints with automatic retry
    and error handling.

    Example:
        ```python
        from glaium import Client

        # Using environment variable GLAIUM_API_KEY
        client = Client()

        # Or with explicit API key
        client = Client(api_key="glaium_org123_ak_xxx")

        # Register an agent
        reg = client.register(
            agent_id="my-agent",
            declared_outputs=[{"name": "revenue"}],
        )

        # Use token for subsequent calls
        agent_client = client.with_token(reg.agent_token)
        optimization = agent_client.get_optimization()
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        data_base_url: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        timeout: float = 30.0,
        token: str | None = None,
    ):
        """
        Initialize the client.

        Args:
            api_key: API key for authentication. Falls back to GLAIUM_API_KEY env var.
            base_url: Base URL for the optimizer API. Falls back to GLAIUM_BASE_URL env var.
            data_base_url: Base URL for the Data Service API. Defaults to base_url.
                Agents on Neo set this to localhost:8004 to avoid external round-trips.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_delay: Initial delay in seconds before first retry.
            retry_backoff: Multiplier for exponential backoff.
            timeout: Request timeout in seconds.
            token: Agent token for authenticated requests (usually set via with_token).
        """
        self._api_key = api_key
        self._base_url = get_base_url(base_url)
        self._data_base_url = data_base_url or self._base_url
        self._timeout = timeout
        self._token = token

        self._retry_config = RetryConfig(
            max_retries=max_retries,
            initial_delay=retry_delay,
            backoff_multiplier=retry_backoff,
        )

        # Lazy-initialized HTTP clients
        self._sync_client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

    def with_token(self, token: str) -> "Client":
        """
        Create a new client instance with an agent token.

        Args:
            token: The agent token from registration.

        Returns:
            New Client instance with token set.
        """
        return Client(
            api_key=self._api_key,
            base_url=self._base_url,
            data_base_url=self._data_base_url,
            max_retries=self._retry_config.max_retries,
            retry_delay=self._retry_config.initial_delay,
            retry_backoff=self._retry_config.backoff_multiplier,
            timeout=self._timeout,
            token=token,
        )

    @property
    def _sync(self) -> httpx.Client:
        """Get or create synchronous HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._sync_client

    @property
    def _async(self) -> httpx.AsyncClient:
        """Get or create asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._async_client

    def _get_headers(self, use_token: bool = False) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}

        if use_token:
            if not self._token:
                raise AuthenticationError("No token set. Use with_token() or register first.")
            headers["Authorization"] = f"Bearer {self._token}"
        else:
            api_key = get_api_key(self._api_key)
            headers["X-API-Key"] = api_key

        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 200:
            return response.json()

        # Try to get error details from response
        try:
            error_body = response.json()
            error_message = error_body.get("detail", str(error_body))
        except Exception:
            error_message = response.text or f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise AuthenticationError(error_message)
        elif response.status_code == 404:
            raise NotFoundError(error_message, status_code=404)
        elif response.status_code == 422 or response.status_code == 400:
            raise ValidationError(error_message, status_code=response.status_code)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                error_message,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif response.status_code >= 500:
            raise ServerError(error_message, status_code=response.status_code)
        else:
            raise APIError(error_message, status_code=response.status_code)

    # =========================================================================
    # Registration
    # =========================================================================

    def register(
        self,
        agent_id: str,
        name: str,
        objective_function: str,
        declared_inputs: list[dict[str, Any] | AgentInput] | None = None,
        declared_outputs: list[dict[str, Any] | AgentOutput] | None = None,
        connections: list[dict[str, Any] | AgentConnection] | None = None,
        formula: str | None = None,
        token_ttl_hours: int = 48,
        dimensions: list[str] | None = None,
        lookback_days: int = 30,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> RegistrationResponse:
        """
        Register an agent with the optimizer.

        Args:
            agent_id: Unique identifier for the agent.
            name: Human-readable agent name (e.g., 'User Acquisition').
            objective_function: Agent's goal/system prompt for LLM reasoning.
            declared_inputs: List of inputs the agent accepts.
            declared_outputs: List of outputs the agent produces.
            connections: Connections to other agents.
            formula: Optional computation formula.
            token_ttl_hours: Token validity period (1-8760 hours).
            dimensions: Dimension fields for data grouping (e.g., ['country', 'platform']).
            lookback_days: Number of days of historical data to fetch (1-365).
            description: Optional description of what this agent does.
            color: Optional hex color for UI display (e.g., '#3b82f6').
            icon: Optional icon name for UI display (e.g., 'users').

        Returns:
            RegistrationResponse with agent token.
        """

        def _do_register() -> RegistrationResponse:
            payload = {
                "agent_id": agent_id,
                "name": name,
                "objective_function": objective_function,
                "declared_inputs": [
                    i.model_dump() if isinstance(i, AgentInput) else i
                    for i in (declared_inputs or [])
                ],
                "declared_outputs": [
                    o.model_dump() if isinstance(o, AgentOutput) else o
                    for o in (declared_outputs or [])
                ],
                "connections": [
                    c.model_dump() if isinstance(c, AgentConnection) else c
                    for c in (connections or [])
                ],
                "formula": formula,
                "token_ttl_hours": token_ttl_hours,
                "dimensions": dimensions or [],
                "lookback_days": lookback_days,
                "description": description,
                "color": color,
                "icon": icon,
            }

            try:
                response = self._sync.post(
                    "/optimizer/register",
                    json=payload,
                    headers=self._get_headers(use_token=False),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            data = self._handle_response(response)
            return RegistrationResponse(**data)

        return retry_sync(_do_register, self._retry_config)

    async def register_async(
        self,
        agent_id: str,
        name: str,
        objective_function: str,
        declared_inputs: list[dict[str, Any] | AgentInput] | None = None,
        declared_outputs: list[dict[str, Any] | AgentOutput] | None = None,
        connections: list[dict[str, Any] | AgentConnection] | None = None,
        formula: str | None = None,
        token_ttl_hours: int = 48,
        dimensions: list[str] | None = None,
        lookback_days: int = 30,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> RegistrationResponse:
        """Async version of register(). See register() for full docstring."""

        async def _do_register() -> RegistrationResponse:
            payload = {
                "agent_id": agent_id,
                "name": name,
                "objective_function": objective_function,
                "declared_inputs": [
                    i.model_dump() if isinstance(i, AgentInput) else i
                    for i in (declared_inputs or [])
                ],
                "declared_outputs": [
                    o.model_dump() if isinstance(o, AgentOutput) else o
                    for o in (declared_outputs or [])
                ],
                "connections": [
                    c.model_dump() if isinstance(c, AgentConnection) else c
                    for c in (connections or [])
                ],
                "formula": formula,
                "token_ttl_hours": token_ttl_hours,
                "dimensions": dimensions or [],
                "lookback_days": lookback_days,
                "description": description,
                "color": color,
                "icon": icon,
            }

            try:
                response = await self._async.post(
                    "/optimizer/register",
                    json=payload,
                    headers=self._get_headers(use_token=False),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            data = self._handle_response(response)
            return RegistrationResponse(**data)

        return await retry_async(_do_register, self._retry_config)

    # =========================================================================
    # Optimization
    # =========================================================================

    def get_optimization(self) -> Optimization:
        """
        Get current optimization (objectives, constraints, search space).

        Requires token authentication (use with_token first).

        Returns:
            Optimization with objectives, constraints, and scheduling info.
        """

        def _do_get() -> Optimization:
            try:
                response = self._sync.get(
                    "/optimizer/optimization",
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            data = self._handle_response(response)
            return Optimization(**data)

        return retry_sync(_do_get, self._retry_config)

    async def get_optimization_async(self) -> Optimization:
        """Async version of get_optimization()."""

        async def _do_get() -> Optimization:
            try:
                response = await self._async.get(
                    "/optimizer/optimization",
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            data = self._handle_response(response)
            return Optimization(**data)

        return await retry_async(_do_get, self._retry_config)

    # =========================================================================
    # Events
    # =========================================================================

    def submit_event(self, event: Event | dict[str, Any]) -> EventResponse:
        """
        Submit an event to the optimizer.

        Requires token authentication (use with_token first).

        Args:
            event: Event to submit (CycleStartEvent, CycleEndEvent, etc.).

        Returns:
            EventResponse with status.
        """

        def _do_submit() -> EventResponse:
            payload = event.model_dump() if hasattr(event, "model_dump") else event

            try:
                response = self._sync.post(
                    "/optimizer/event",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            data = self._handle_response(response)
            return EventResponse(**data)

        return retry_sync(_do_submit, self._retry_config)

    async def submit_event_async(self, event: Event | dict[str, Any]) -> EventResponse:
        """Async version of submit_event()."""

        async def _do_submit() -> EventResponse:
            payload = event.model_dump() if hasattr(event, "model_dump") else event

            try:
                response = await self._async.post(
                    "/optimizer/event",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            data = self._handle_response(response)
            return EventResponse(**data)

        return await retry_async(_do_submit, self._retry_config)

    # =========================================================================
    # Hands-Up Feedback (for learning from human decisions)
    # =========================================================================

    def get_hands_up_feedback(
        self,
        agent_id: str,
        since_cycle: int | None = None,
        limit: int = 10,
    ) -> HandsUpFeedbackResponse:
        """
        Get feedback from resolved hands-up items.

        This enables a learning loop where the agent can see how humans
        responded to its previous recommendations.

        Requires token authentication (use with_token first).

        Args:
            agent_id: The agent slug to get feedback for.
            since_cycle: Only get feedback resolved since this cycle number.
            limit: Maximum number of feedback items to return.

        Returns:
            HandsUpFeedbackResponse with resolved recommendations and their outcomes.

        Example:
            ```python
            feedback = client.get_hands_up_feedback(
                agent_id="user_acquisition",
                since_cycle=previous_cycle_number,
            )

            if feedback.feedback:
                for item in feedback.feedback:
                    if item.resolution == "approved":
                        # Human approved this recommendation
                        pass
                    elif item.resolution == "rejected":
                        # Human rejected - learn from this
                        pass
            ```
        """

        def _do_get() -> HandsUpFeedbackResponse:
            params = {"agent_id": agent_id, "limit": limit}
            if since_cycle is not None:
                params["since_cycle"] = since_cycle

            try:
                response = self._sync.get(
                    "/optimizer/hands_up/feedback",
                    params=params,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            data = self._handle_response(response)
            return HandsUpFeedbackResponse(**data)

        return retry_sync(_do_get, self._retry_config)

    async def get_hands_up_feedback_async(
        self,
        agent_id: str,
        since_cycle: int | None = None,
        limit: int = 10,
    ) -> HandsUpFeedbackResponse:
        """Async version of get_hands_up_feedback(). See get_hands_up_feedback() for full docstring."""

        async def _do_get() -> HandsUpFeedbackResponse:
            params = {"agent_id": agent_id, "limit": limit}
            if since_cycle is not None:
                params["since_cycle"] = since_cycle

            try:
                response = await self._async.get(
                    "/optimizer/hands_up/feedback",
                    params=params,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            data = self._handle_response(response)
            return HandsUpFeedbackResponse(**data)

        return await retry_async(_do_get, self._retry_config)

    # =========================================================================
    # Agent Config
    # =========================================================================

    def get_agent_config(self) -> dict[str, Any]:
        """
        Get agent's stored config from the Optimizer.

        Returns the agent's objective_function, declared_inputs, declared_outputs,
        connections, constraints, config, resources, dimensions, lookback_days, etc.

        Requires token authentication.
        """

        def _do_get() -> dict[str, Any]:
            try:
                response = self._sync.get(
                    "/optimizer/agent-config",
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return retry_sync(_do_get, self._retry_config)

    async def get_agent_config_async(self) -> dict[str, Any]:
        """Async version of get_agent_config()."""

        async def _do_get() -> dict[str, Any]:
            try:
                response = await self._async.get(
                    "/optimizer/agent-config",
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_get, self._retry_config)

    # =========================================================================
    # Data Retrieval
    # =========================================================================

    def retrieve_data(
        self,
        metrics: list[str],
        dimensions: list[str] | None = None,
        period: list[str] | None = None,
        conditional: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve metrics data from the Data Service.

        Args:
            metrics: Metric names to retrieve.
            dimensions: Dimension fields to group by.
            period: Date range [start, end] in YYYY-MM-DD format.
            conditional: Filter expression.

        Returns:
            Data response dict with rows, totals, etc.
        """

        def _do_get() -> dict[str, Any]:
            params: dict[str, Any] = {"metrics": ",".join(metrics)}
            if dimensions:
                params["dimensions"] = ",".join(dimensions)
            if period:
                params["period"] = ",".join(period)
            if conditional:
                params["conditional"] = conditional

            try:
                # Use data_base_url for data service calls
                client = httpx.Client(
                    base_url=self._data_base_url,
                    timeout=self._timeout,
                )
                response = client.get(
                    "/retrieve",
                    params=params,
                    headers=self._get_headers(use_token=True),
                )
                client.close()
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._data_base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return retry_sync(_do_get, self._retry_config)

    async def retrieve_data_async(
        self,
        metrics: list[str],
        dimensions: list[str] | None = None,
        period: list[str] | None = None,
        conditional: str | None = None,
    ) -> dict[str, Any]:
        """Async version of retrieve_data()."""

        async def _do_get() -> dict[str, Any]:
            params: dict[str, Any] = {"metrics": ",".join(metrics)}
            if dimensions:
                params["dimensions"] = ",".join(dimensions)
            if period:
                params["period"] = ",".join(period)
            if conditional:
                params["conditional"] = conditional

            try:
                client = httpx.AsyncClient(
                    base_url=self._data_base_url,
                    timeout=self._timeout,
                )
                response = await client.get(
                    "/retrieve",
                    params=params,
                    headers=self._get_headers(use_token=True),
                )
                await client.aclose()
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._data_base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_get, self._retry_config)

    # =========================================================================
    # LLM Reasoning (async submit-and-poll)
    # =========================================================================

    def reason(
        self,
        data_context: dict[str, Any],
        memory_context: str | None = None,
        feedback_context: dict | None = None,
        tier: str = "balanced",
        poll_interval: float = 2.0,
        timeout: float = 180.0,
    ) -> dict[str, Any]:
        """
        Submit LLM reasoning request and poll until complete.

        Sync wrapper — blocks until result is ready.

        Args:
            data_context: Data from data retrieval.
            memory_context: Past decisions and outcomes.
            feedback_context: Human feedback on previous recommendations.
            tier: Model tier (fast/balanced/powerful).
            poll_interval: Seconds between poll requests.
            timeout: Max seconds to wait for result.

        Returns:
            Reasoning result dict with recommendations, analysis, etc.

        Raises:
            ReasoningError: Reasoning failed on the server.
            ReasoningTimeoutError: Timed out waiting for result.
        """

        def _do_reason() -> dict[str, Any]:
            payload = {
                "data_context": data_context,
                "memory_context": memory_context,
                "feedback_context": feedback_context,
                "tier": tier,
            }

            # Submit
            try:
                response = self._sync.post(
                    "/optimizer/reason",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            job = self._handle_response(response)
            request_id = job["request_id"]

            # Poll
            import time
            elapsed = 0.0
            while elapsed < timeout:
                time.sleep(poll_interval)
                elapsed += poll_interval

                try:
                    poll_response = self._sync.get(
                        f"/optimizer/reason/{request_id}",
                        headers=self._get_headers(use_token=True),
                    )
                except httpx.ConnectError as e:
                    raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
                except httpx.TimeoutException as e:
                    raise TimeoutError(f"Request timed out: {e}")

                status = self._handle_response(poll_response)
                if status["status"] == "completed":
                    return status["result"]
                if status["status"] == "failed":
                    raise ReasoningError(
                        status.get("error", "Reasoning failed"),
                        details={"message": status.get("message")},
                    )

            raise ReasoningTimeoutError(
                f"Reasoning request {request_id} timed out after {timeout}s"
            )

        return retry_sync(_do_reason, self._retry_config)

    async def reason_async(
        self,
        data_context: dict[str, Any],
        memory_context: str | None = None,
        feedback_context: dict | None = None,
        tier: str = "balanced",
        poll_interval: float = 2.0,
        timeout: float = 180.0,
    ) -> dict[str, Any]:
        """
        Async submit LLM reasoning request and poll until complete.

        Args:
            data_context: Data from data retrieval.
            memory_context: Past decisions and outcomes.
            feedback_context: Human feedback on previous recommendations.
            tier: Model tier (fast/balanced/powerful).
            poll_interval: Seconds between poll requests.
            timeout: Max seconds to wait for result.

        Returns:
            Reasoning result dict with recommendations, analysis, etc.

        Raises:
            ReasoningError: Reasoning failed on the server.
            ReasoningTimeoutError: Timed out waiting for result.
        """
        payload = {
            "data_context": data_context,
            "memory_context": memory_context,
            "feedback_context": feedback_context,
            "tier": tier,
        }

        # Submit
        try:
            response = await self._async.post(
                "/optimizer/reason",
                json=payload,
                headers=self._get_headers(use_token=True),
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")

        job = self._handle_response(response)
        request_id = job["request_id"]

        # Poll
        elapsed = 0.0
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            try:
                poll_response = await self._async.get(
                    f"/optimizer/reason/{request_id}",
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            status = self._handle_response(poll_response)
            if status["status"] == "completed":
                return status["result"]
            if status["status"] == "failed":
                raise ReasoningError(
                    status.get("error", "Reasoning failed"),
                    details={"message": status.get("message")},
                )

        raise ReasoningTimeoutError(
            f"Reasoning request {request_id} timed out after {timeout}s"
        )

    # =========================================================================
    # LLM Verification (async submit-and-poll)
    # =========================================================================

    def verify(
        self,
        recommendation: dict[str, Any],
        data_context: dict[str, Any],
        risk_level: str = "low",
        poll_interval: float = 2.0,
        timeout: float = 120.0,
    ) -> dict[str, Any]:
        """
        Submit verification request and poll until complete.

        Sync wrapper — blocks until result is ready.

        Args:
            recommendation: The recommendation to verify.
            data_context: Data context for verification.
            risk_level: Risk level (low/medium/high).
            poll_interval: Seconds between poll requests.
            timeout: Max seconds to wait for result.

        Returns:
            Verification result dict with approved, reasoning, etc.

        Raises:
            VerificationError: Verification failed on the server.
            ReasoningTimeoutError: Timed out waiting for result.
        """

        def _do_verify() -> dict[str, Any]:
            payload = {
                "recommendation": recommendation,
                "data_context": data_context,
                "risk_level": risk_level,
            }

            # Submit
            try:
                response = self._sync.post(
                    "/optimizer/verify",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            job = self._handle_response(response)
            request_id = job["request_id"]

            # Poll
            import time
            elapsed = 0.0
            while elapsed < timeout:
                time.sleep(poll_interval)
                elapsed += poll_interval

                try:
                    poll_response = self._sync.get(
                        f"/optimizer/verify/{request_id}",
                        headers=self._get_headers(use_token=True),
                    )
                except httpx.ConnectError as e:
                    raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
                except httpx.TimeoutException as e:
                    raise TimeoutError(f"Request timed out: {e}")

                status = self._handle_response(poll_response)
                if status["status"] == "completed":
                    return status["result"]
                if status["status"] == "failed":
                    raise VerificationError(
                        status.get("error", "Verification failed"),
                    )

            raise ReasoningTimeoutError(
                f"Verify request {request_id} timed out after {timeout}s"
            )

        return retry_sync(_do_verify, self._retry_config)

    async def verify_async(
        self,
        recommendation: dict[str, Any],
        data_context: dict[str, Any],
        risk_level: str = "low",
        poll_interval: float = 2.0,
        timeout: float = 120.0,
    ) -> dict[str, Any]:
        """Async version of verify(). See verify() for full docstring."""
        payload = {
            "recommendation": recommendation,
            "data_context": data_context,
            "risk_level": risk_level,
        }

        # Submit
        try:
            response = await self._async.post(
                "/optimizer/verify",
                json=payload,
                headers=self._get_headers(use_token=True),
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")

        job = self._handle_response(response)
        request_id = job["request_id"]

        # Poll
        elapsed = 0.0
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            try:
                poll_response = await self._async.get(
                    f"/optimizer/verify/{request_id}",
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            status = self._handle_response(poll_response)
            if status["status"] == "completed":
                return status["result"]
            if status["status"] == "failed":
                raise VerificationError(
                    status.get("error", "Verification failed"),
                )

        raise ReasoningTimeoutError(
            f"Verify request {request_id} timed out after {timeout}s"
        )

    # =========================================================================
    # Execution Management
    # =========================================================================

    async def update_execution_async(
        self,
        execution_id: int,
        model: str | None = None,
        tokens: dict | None = None,
        cost_usd: float | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Update execution with LLM usage info or status."""
        payload: dict[str, Any] = {"execution_id": execution_id}
        if model is not None:
            payload["model"] = model
        if tokens is not None:
            payload["tokens"] = tokens
        if cost_usd is not None:
            payload["cost_usd"] = cost_usd
        if status is not None:
            payload["status"] = status

        async def _do_update() -> dict[str, Any]:
            try:
                response = await self._async.patch(
                    "/optimizer/execution",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_update, self._retry_config)

    async def complete_execution_async(
        self,
        execution_id: int,
        status: str = "completed",
        actions_taken: int = 0,
        actions_skipped: int = 0,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        """Mark execution as completed with final status."""
        payload = {
            "execution_id": execution_id,
            "status": status,
            "actions_taken": actions_taken,
            "actions_skipped": actions_skipped,
            "error_message": error_message,
        }

        async def _do_complete() -> dict[str, Any]:
            try:
                response = await self._async.post(
                    "/optimizer/execution/complete",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_complete, self._retry_config)

    async def record_action_async(
        self,
        execution_id: int,
        action_type: str,
        target: str,
        parameters: dict | None = None,
        status: str = "approved",
        result: dict | None = None,
    ) -> dict[str, Any]:
        """Record an action taken within an execution."""
        payload = {
            "execution_id": execution_id,
            "action_type": action_type,
            "target": target,
            "parameters": parameters,
            "status": status,
            "result": result,
        }

        async def _do_record() -> dict[str, Any]:
            try:
                response = await self._async.post(
                    "/optimizer/execution/action",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_record, self._retry_config)

    async def get_execution_async(
        self,
        execution_id: int,
    ) -> dict[str, Any]:
        """Get execution record by ID."""

        async def _do_get() -> dict[str, Any]:
            try:
                response = await self._async.get(
                    f"/optimizer/execution/{execution_id}",
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_get, self._retry_config)

    # =========================================================================
    # Notifications
    # =========================================================================

    async def create_notification_async(
        self,
        kind: str,
        notification: str,
        origin: str | None = None,
        url: str | None = None,
    ) -> dict[str, Any]:
        """Create a notification."""
        payload: dict[str, Any] = {
            "kind": kind,
            "notification": notification,
        }
        if origin is not None:
            payload["origin"] = origin
        if url is not None:
            payload["url"] = url

        async def _do_create() -> dict[str, Any]:
            try:
                response = await self._async.post(
                    "/optimizer/notification",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_create, self._retry_config)

    async def update_notification_async(
        self,
        notification_id: int,
        action_taken: str | None = None,
    ) -> dict[str, Any]:
        """Update a notification (e.g., mark as actioned)."""
        payload: dict[str, Any] = {"notification_id": notification_id}
        if action_taken is not None:
            payload["action_taken"] = action_taken

        async def _do_update() -> dict[str, Any]:
            try:
                response = await self._async.patch(
                    "/optimizer/notification",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_update, self._retry_config)

    # =========================================================================
    # Deanonymization
    # =========================================================================

    async def deanonymize_async(
        self,
        data: list[dict],
        dimensions: list[str],
    ) -> list[dict]:
        """De-anonymize dimension values via the Data Service."""

        async def _do_deanonymize() -> list[dict]:
            payload = {"data": data, "dimensions": dimensions}

            try:
                client = httpx.AsyncClient(
                    base_url=self._data_base_url,
                    timeout=self._timeout,
                )
                response = await client.post(
                    "/deanonymize",
                    json=payload,
                    headers=self._get_headers(use_token=True),
                )
                await client.aclose()
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._data_base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_deanonymize, self._retry_config)

    # =========================================================================
    # Deregistration
    # =========================================================================

    def deregister(self) -> dict[str, Any]:
        """
        Deregister the agent from the optimizer.

        Requires token authentication (use with_token first).

        Returns:
            Response with deregistration status.
        """

        def _do_deregister() -> dict[str, Any]:
            try:
                response = self._sync.delete(
                    "/optimizer/register",
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return retry_sync(_do_deregister, self._retry_config)

    async def deregister_async(self) -> dict[str, Any]:
        """Async version of deregister()."""

        async def _do_deregister() -> dict[str, Any]:
            try:
                response = await self._async.delete(
                    "/optimizer/register",
                    headers=self._get_headers(use_token=True),
                )
            except httpx.ConnectError as e:
                raise ConnectionError(f"Failed to connect to {self._base_url}: {e}")
            except httpx.TimeoutException as e:
                raise TimeoutError(f"Request timed out: {e}")

            return self._handle_response(response)

        return await retry_async(_do_deregister, self._retry_config)

    # =========================================================================
    # Cleanup
    # =========================================================================

    def close(self) -> None:
        """Close the client and release resources."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    async def aclose(self) -> None:
        """Async close the client and release resources."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
