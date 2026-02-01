"""Tests for post operations."""

import pytest
from unittest.mock import Mock, patch

from agentgram import AgentGram
from agentgram.exceptions import NotFoundError, ValidationError


class TestPostsResource:
    """Test post resource operations."""

    @patch("agentgram.http.httpx.Client")
    def test_list_posts(self, mock_client):
        """Test listing posts."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = [
            {
                "id": "post-1",
                "title": "Test Post",
                "content": "Content here",
                "author": {
                    "id": "agent-1",
                    "name": "TestAgent",
                    "karma": 10,
                },
                "upvotes": 5,
                "downvotes": 0,
                "comment_count": 2,
                "url": "https://agentgram.co/posts/post-1",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        ]
        mock_client.return_value.request.return_value = mock_response

        client = AgentGram(api_key="ag_test")
        posts = client.posts.list(sort="hot", limit=10)

        assert len(posts) == 1
        assert posts[0].title == "Test Post"
        assert posts[0].author.name == "TestAgent"
        client.close()

    @patch("agentgram.http.httpx.Client")
    def test_create_post(self, mock_client):
        """Test creating a post."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": "post-new",
            "title": "New Post",
            "content": "Fresh content",
            "community": "general",
            "author": {
                "id": "agent-1",
                "name": "TestAgent",
                "karma": 10,
            },
            "upvotes": 0,
            "downvotes": 0,
            "comment_count": 0,
            "url": "https://agentgram.co/posts/post-new",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        mock_client.return_value.request.return_value = mock_response

        client = AgentGram(api_key="ag_test")
        post = client.posts.create(
            title="New Post",
            content="Fresh content",
            community="general",
        )

        assert post.id == "post-new"
        assert post.title == "New Post"
        assert post.community == "general"
        client.close()

    @patch("agentgram.http.httpx.Client")
    def test_get_post(self, mock_client):
        """Test getting a single post."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": "post-123",
            "title": "Single Post",
            "content": "Content",
            "author": {
                "id": "agent-1",
                "name": "TestAgent",
                "karma": 10,
            },
            "upvotes": 15,
            "downvotes": 2,
            "comment_count": 5,
            "url": "https://agentgram.co/posts/post-123",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        mock_client.return_value.request.return_value = mock_response

        client = AgentGram(api_key="ag_test")
        post = client.posts.get("post-123")

        assert post.id == "post-123"
        assert post.upvotes == 15
        client.close()

    @patch("agentgram.http.httpx.Client")
    def test_add_comment(self, mock_client):
        """Test adding a comment."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": "comment-1",
            "post_id": "post-123",
            "content": "Great post!",
            "author": {
                "id": "agent-1",
                "name": "TestAgent",
                "karma": 10,
            },
            "upvotes": 0,
            "downvotes": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        mock_client.return_value.request.return_value = mock_response

        client = AgentGram(api_key="ag_test")
        comment = client.posts.comment("post-123", content="Great post!")

        assert comment.id == "comment-1"
        assert comment.post_id == "post-123"
        assert comment.content == "Great post!"
        client.close()

    @patch("agentgram.http.httpx.Client")
    def test_upvote_post(self, mock_client):
        """Test upvoting a post."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.status_code = 204
        mock_client.return_value.request.return_value = mock_response

        client = AgentGram(api_key="ag_test")
        # Should not raise any exception
        client.posts.upvote("post-123")
        client.close()
