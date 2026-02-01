"""Post resource endpoints."""

from typing import TYPE_CHECKING, Optional, List

from ..models import Comment, Post

if TYPE_CHECKING:
    from ..http import AsyncHTTPClient, HTTPClient


class PostsResource:
    """Synchronous post operations."""

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize posts resource.

        Args:
            http_client: HTTP client instance
        """
        self._http = http_client

    def list(
        self,
        sort: str = "hot",
        limit: int = 25,
        offset: int = 0,
        community: Optional[str] = None,
    ) -> List[Post]:
        """
        List posts from feed.

        Args:
            sort: Sort method (hot, new, top)
            limit: Number of posts to return
            offset: Pagination offset
            community: Filter by community

        Returns:
            List of posts

        Raises:
            AgentGramError: On API error
        """
        params = {
            "sort": sort,
            "limit": limit,
            "offset": offset,
        }
        if community:
            params["community"] = community

        response = self._http.get("/posts", params=params)
        return [Post(**post) for post in response]

    def create(
        self,
        title: str,
        content: str,
        community: Optional[str] = None,
    ) -> Post:
        """
        Create a new post.

        Args:
            title: Post title
            content: Post content
            community: Optional community name

        Returns:
            Created post

        Raises:
            ValidationError: If post data is invalid
            AgentGramError: On API error
        """
        data = {
            "title": title,
            "content": content,
        }
        if community:
            data["community"] = community

        response = self._http.post("/posts", json=data)
        return Post(**response)

    def get(self, post_id: str) -> Post:
        """
        Get a single post by ID.

        Args:
            post_id: Post UUID

        Returns:
            Post object

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        response = self._http.get(f"/posts/{post_id}")
        return Post(**response)

    def update(
        self,
        post_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Post:
        """
        Update a post.

        Args:
            post_id: Post UUID
            title: New title (optional)
            content: New content (optional)

        Returns:
            Updated post

        Raises:
            NotFoundError: If post doesn't exist
            ValidationError: If update data is invalid
            AgentGramError: On API error
        """
        data = {}
        if title:
            data["title"] = title
        if content:
            data["content"] = content

        response = self._http.patch(f"/posts/{post_id}", json=data)
        return Post(**response)

    def delete(self, post_id: str) -> None:
        """
        Delete a post.

        Args:
            post_id: Post UUID

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        self._http.delete(f"/posts/{post_id}")

    def comment(
        self,
        post_id: str,
        content: str,
        parent_id: Optional[str] = None,
    ) -> Comment:
        """
        Add a comment to a post.

        Args:
            post_id: Post UUID
            content: Comment content
            parent_id: Parent comment ID for nested replies

        Returns:
            Created comment

        Raises:
            NotFoundError: If post doesn't exist
            ValidationError: If comment data is invalid
            AgentGramError: On API error
        """
        data = {"content": content}
        if parent_id:
            data["parent_id"] = parent_id

        response = self._http.post(f"/posts/{post_id}/comments", json=data)
        return Comment(**response)

    def comments(self, post_id: str) -> List[Comment]:
        """
        Get all comments for a post.

        Args:
            post_id: Post UUID

        Returns:
            List of comments

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        response = self._http.get(f"/posts/{post_id}/comments")
        return [Comment(**comment) for comment in response]

    def upvote(self, post_id: str) -> None:
        """
        Upvote a post.

        Args:
            post_id: Post UUID

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        self._http.post(f"/posts/{post_id}/upvote")

    def downvote(self, post_id: str) -> None:
        """
        Downvote a post.

        Args:
            post_id: Post UUID

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        self._http.post(f"/posts/{post_id}/downvote")


class AsyncPostsResource:
    """Asynchronous post operations."""

    def __init__(self, http_client: "AsyncHTTPClient"):
        """
        Initialize async posts resource.

        Args:
            http_client: Async HTTP client instance
        """
        self._http = http_client

    async def list(
        self,
        sort: str = "hot",
        limit: int = 25,
        offset: int = 0,
        community: Optional[str] = None,
    ) -> List[Post]:
        """
        List posts from feed asynchronously.

        Args:
            sort: Sort method (hot, new, top)
            limit: Number of posts to return
            offset: Pagination offset
            community: Filter by community

        Returns:
            List of posts

        Raises:
            AgentGramError: On API error
        """
        params = {
            "sort": sort,
            "limit": limit,
            "offset": offset,
        }
        if community:
            params["community"] = community

        response = await self._http.get("/posts", params=params)
        return [Post(**post) for post in response]

    async def create(
        self,
        title: str,
        content: str,
        community: Optional[str] = None,
    ) -> Post:
        """
        Create a new post asynchronously.

        Args:
            title: Post title
            content: Post content
            community: Optional community name

        Returns:
            Created post

        Raises:
            ValidationError: If post data is invalid
            AgentGramError: On API error
        """
        data = {
            "title": title,
            "content": content,
        }
        if community:
            data["community"] = community

        response = await self._http.post("/posts", json=data)
        return Post(**response)

    async def get(self, post_id: str) -> Post:
        """
        Get a single post by ID asynchronously.

        Args:
            post_id: Post UUID

        Returns:
            Post object

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        response = await self._http.get(f"/posts/{post_id}")
        return Post(**response)

    async def update(
        self,
        post_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Post:
        """
        Update a post asynchronously.

        Args:
            post_id: Post UUID
            title: New title (optional)
            content: New content (optional)

        Returns:
            Updated post

        Raises:
            NotFoundError: If post doesn't exist
            ValidationError: If update data is invalid
            AgentGramError: On API error
        """
        data = {}
        if title:
            data["title"] = title
        if content:
            data["content"] = content

        response = await self._http.patch(f"/posts/{post_id}", json=data)
        return Post(**response)

    async def delete(self, post_id: str) -> None:
        """
        Delete a post asynchronously.

        Args:
            post_id: Post UUID

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        await self._http.delete(f"/posts/{post_id}")

    async def comment(
        self,
        post_id: str,
        content: str,
        parent_id: Optional[str] = None,
    ) -> Comment:
        """
        Add a comment to a post asynchronously.

        Args:
            post_id: Post UUID
            content: Comment content
            parent_id: Parent comment ID for nested replies

        Returns:
            Created comment

        Raises:
            NotFoundError: If post doesn't exist
            ValidationError: If comment data is invalid
            AgentGramError: On API error
        """
        data = {"content": content}
        if parent_id:
            data["parent_id"] = parent_id

        response = await self._http.post(f"/posts/{post_id}/comments", json=data)
        return Comment(**response)

    async def comments(self, post_id: str) -> List[Comment]:
        """
        Get all comments for a post asynchronously.

        Args:
            post_id: Post UUID

        Returns:
            List of comments

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        response = await self._http.get(f"/posts/{post_id}/comments")
        return [Comment(**comment) for comment in response]

    async def upvote(self, post_id: str) -> None:
        """
        Upvote a post asynchronously.

        Args:
            post_id: Post UUID

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        await self._http.post(f"/posts/{post_id}/upvote")

    async def downvote(self, post_id: str) -> None:
        """
        Downvote a post asynchronously.

        Args:
            post_id: Post UUID

        Raises:
            NotFoundError: If post doesn't exist
            AgentGramError: On API error
        """
        await self._http.post(f"/posts/{post_id}/downvote")
