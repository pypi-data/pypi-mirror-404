"""
Pamela Enterprise API Client for Python
"""

from typing import Optional, Dict, List, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pamela.exceptions import (
    PamelaError,
    AuthenticationError,
    SubscriptionError,
    RateLimitError,
    ValidationError,
    CallError,
)


class UsageClient:
    """Usage client for querying usage statistics."""

    def __init__(self, client: "PamelaClient"):
        """Initialize usage client with parent client."""
        self._client = client

    def get(self, period: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for partner/project.

        Args:
            period: Optional billing period (YYYY-MM format). If not provided, returns current month.

        Returns:
            Usage statistics with call_count, quota info, etc.
        """
        return self._client.get_usage(period)


class PamelaClient:
    """Client for Pamela Enterprise Voice API."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Pamela client.

        Args:
            api_key: Enterprise API key (pk_live_xxx)
            base_url: Optional base URL (defaults to https://api.thisispamela.com)
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.thisispamela.com"
        self.base_api_url = f"{self.base_url}/api/b2b/v1"

        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

        # Initialize usage client
        self.usage = UsageClient(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base path)
            data: Request body
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_api_url}{endpoint}"
        response = self.session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            timeout=30,
        )
        if response.status_code >= 400:
            self._raise_for_error(response, endpoint)
        return response.json()

    def _raise_for_error(self, response: requests.Response, endpoint: str) -> None:
        """
        Raise a structured SDK exception based on API error response.

        Args:
            response: requests.Response object
            endpoint: API endpoint for context
        """
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        error_code = None
        message = None
        details: Dict[str, Any] = {}

        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, dict):
                error_code = detail.get("error_code") or detail.get("error", {}).get("code")
                message = detail.get("message") or detail.get("error", {}).get("message")
                details = detail.get("details") or detail.get("error", {}).get("details") or {}
            else:
                error_code = payload.get("error_code") or payload.get("error", {}).get("code")
                message = payload.get("message") or payload.get("detail")
                details = payload.get("details") or payload.get("error", {}).get("details") or {}

        if not message:
            message = f"Request failed with status {response.status_code}"

        status_code = response.status_code
        if status_code == 401:
            raise AuthenticationError(message, error_code=error_code, details=details, status_code=status_code)
        if status_code == 403:
            raise SubscriptionError(message, error_code=error_code, details=details, status_code=status_code)
        if status_code == 429:
            raise RateLimitError(message, error_code=error_code, details=details, status_code=status_code)
        if status_code in (400, 422):
            raise ValidationError(message, error_code=error_code, details=details, status_code=status_code)

        # Use CallError for call endpoints
        if endpoint.startswith("/calls"):
            raise CallError(message, error_code=error_code, details=details, status_code=status_code)

        raise PamelaError(message, error_code=error_code, details=details, status_code=status_code)

    def create_call(
        self,
        to: str,
        task: str,
        country: Optional[str] = None,
        locale: Optional[str] = None,
        instructions: Optional[str] = None,
        max_duration_seconds: Optional[int] = None,
        voice: Optional[str] = None,
        agent_name: Optional[str] = None,
        caller_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        webhooks: Optional[Dict[str, str]] = None,
        end_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new call.

        Args:
            to: Destination phone number (E.164 format)
            task: Task description for the call
            country: Optional ISO 3166-1 alpha-2 country code
            locale: Optional locale (e.g., en-US)
            instructions: Optional additional instructions
            max_duration_seconds: Optional max call duration in seconds
            voice: Optional voice preference ("male", "female", or "auto")
            agent_name: Optional agent name override
            caller_name: Optional name of who the agent is calling on behalf of
            metadata: Optional metadata dict
            tools: Optional list of tools
            webhooks: Optional webhook overrides
            end_user_id: Optional end-user ID for marketplace/tenant isolation (privacy/context)

        Returns:
            Call response with id, status, call_session_id, created_at
        """
        data = {
            "to": to,
            "task": task,
        }
        if country:
            data["country"] = country
        if locale:
            data["locale"] = locale
        if instructions:
            data["instructions"] = instructions
        if max_duration_seconds is not None:
            data["max_duration_seconds"] = max_duration_seconds
        if voice:
            data["voice"] = voice
        if agent_name:
            data["agent_name"] = agent_name
        if caller_name:
            data["caller_name"] = caller_name
        if metadata:
            data["metadata"] = metadata
        if tools:
            data["tools"] = tools
        if webhooks:
            data["webhooks"] = webhooks
        if end_user_id:
            data["end_user_id"] = end_user_id

        return self._request("POST", "/calls", data=data)

    def get_call(self, call_id: str) -> Dict[str, Any]:
        """
        Get call status and details.

        Args:
            call_id: Call ID

        Returns:
            Call status with transcript, summary, etc.
        """
        return self._request("GET", f"/calls/{call_id}")

    def cancel_call(self, call_id: str) -> Dict[str, Any]:
        """
        Cancel an in-progress call.

        Args:
            call_id: Call ID

        Returns:
            Success response
        """
        return self._request("POST", f"/calls/{call_id}/cancel")

    def hangup_call(self, call_id: str) -> Dict[str, Any]:
        """
        Force hangup an in-progress call.

        Args:
            call_id: Call ID

        Returns:
            Success response
        """
        return self._request("POST", f"/calls/{call_id}/hangup")

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Optional[Dict[str, Any]] = None,
        timeout_ms: int = 30000,
    ) -> Dict[str, Any]:
        """
        Register a tool for the project.

        Args:
            name: Tool name
            description: Tool description
            input_schema: JSON Schema for inputs
            output_schema: Optional JSON Schema for outputs
            timeout_ms: Timeout in milliseconds

        Returns:
            Tool registration response
        """
        data = {
            "tool": {
                "name": name,
                "description": description,
                "input_schema": input_schema,
                "output_schema": output_schema or {},
                "timeout_ms": timeout_ms,
            }
        }
        return self._request("POST", "/tools", data=data)

    def list_calls(
        self,
        status: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List calls for the authenticated partner/project.

        Args:
            status: Optional filter by status (queued, ringing, in_progress, completed, failed, cancelled)
            status_filter: Optional filter by status (preferred alias for status)
            limit: Optional limit number of results (default: 50, max: 100)
            offset: Optional offset for pagination
            start_date: Optional start date filter (ISO 8601 format)
            end_date: Optional end date filter (ISO 8601 format)

        Returns:
            Dictionary with calls list and pagination info
        """
        params = {}
        if status_filter:
            params["status_filter"] = status_filter
        elif status:
            params["status_filter"] = status
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._request("GET", "/calls", params=params)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all tools for the project.

        Returns:
            List of tool definitions
        """
        return self._request("GET", "/tools")

    def delete_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Delete (deactivate) a tool.

        Args:
            tool_id: Tool ID

        Returns:
            Success response
        """
        return self._request("DELETE", f"/tools/{tool_id}")

    def get_usage(self, period: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for partner/project.

        Args:
            period: Optional billing period (YYYY-MM format). If not provided, returns current month.

        Returns:
            Usage statistics with call_count, quota info, etc.
        """
        params = {}
        if period:
            params["period"] = period
        return self._request("GET", "/usage", params=params)
