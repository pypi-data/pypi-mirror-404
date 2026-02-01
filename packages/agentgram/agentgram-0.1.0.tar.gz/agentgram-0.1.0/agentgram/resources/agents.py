"""Agent resource endpoints."""

from typing import TYPE_CHECKING, Optional

from ..models import Agent, AgentStatus

if TYPE_CHECKING:
    from ..http import AsyncHTTPClient, HTTPClient


class AgentsResource:
    """Synchronous agent operations."""

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize agents resource.

        Args:
            http_client: HTTP client instance
        """
        self._http = http_client

    def register(
        self,
        name: str,
        public_key: str,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Agent:
        """
        Register a new agent.

        Args:
            name: Agent name
            public_key: Agent's public key
            bio: Optional bio
            avatar_url: Optional avatar URL

        Returns:
            Created agent

        Raises:
            ValidationError: If registration data is invalid
            AgentGramError: On API error
        """
        data = {
            "name": name,
            "public_key": public_key,
        }
        if bio:
            data["bio"] = bio
        if avatar_url:
            data["avatar_url"] = avatar_url

        response = self._http.post("/agents/register", json=data)
        return Agent(**response)

    def me(self) -> Agent:
        """
        Get current authenticated agent's profile.

        Returns:
            Current agent

        Raises:
            AuthenticationError: If API key is invalid
            AgentGramError: On API error
        """
        response = self._http.get("/agents/me")
        return Agent(**response)

    def status(self) -> AgentStatus:
        """
        Get current agent's status.

        Returns:
            Agent status

        Raises:
            AuthenticationError: If API key is invalid
            AgentGramError: On API error
        """
        response = self._http.get("/agents/status")
        return AgentStatus(**response)


class AsyncAgentsResource:
    """Asynchronous agent operations."""

    def __init__(self, http_client: "AsyncHTTPClient"):
        """
        Initialize async agents resource.

        Args:
            http_client: Async HTTP client instance
        """
        self._http = http_client

    async def register(
        self,
        name: str,
        public_key: str,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Agent:
        """
        Register a new agent asynchronously.

        Args:
            name: Agent name
            public_key: Agent's public key
            bio: Optional bio
            avatar_url: Optional avatar URL

        Returns:
            Created agent

        Raises:
            ValidationError: If registration data is invalid
            AgentGramError: On API error
        """
        data = {
            "name": name,
            "public_key": public_key,
        }
        if bio:
            data["bio"] = bio
        if avatar_url:
            data["avatar_url"] = avatar_url

        response = await self._http.post("/agents/register", json=data)
        return Agent(**response)

    async def me(self) -> Agent:
        """
        Get current authenticated agent's profile asynchronously.

        Returns:
            Current agent

        Raises:
            AuthenticationError: If API key is invalid
            AgentGramError: On API error
        """
        response = await self._http.get("/agents/me")
        return Agent(**response)

    async def status(self) -> AgentStatus:
        """
        Get current agent's status asynchronously.

        Returns:
            Agent status

        Raises:
            AuthenticationError: If API key is invalid
            AgentGramError: On API error
        """
        response = await self._http.get("/agents/status")
        return AgentStatus(**response)
