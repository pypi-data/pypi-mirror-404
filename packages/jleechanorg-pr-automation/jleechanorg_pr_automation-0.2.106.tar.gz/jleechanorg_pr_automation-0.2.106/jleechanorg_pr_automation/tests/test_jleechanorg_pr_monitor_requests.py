#!/usr/bin/env python3
"""Unit tests for jleechanorg_pr_monitor using Python requests instead of gh CLI."""

import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import requests

from automation.jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestDiscoverOpenPRsWithRequests:
    """Test discover_open_prs() using Python requests instead of gh CLI."""

    def test_discover_open_prs_success(self, monkeypatch):
        """Test discover_open_prs successfully fetches PRs via GraphQL API."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        # Mock get_github_token
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock GraphQL API response
        mock_response = Mock()
        mock_response.status_code = 200
        from datetime import datetime, timedelta, timezone
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        mock_response.json.return_value = {
            "data": {
                "search": {
                    "nodes": [
                        {
                            "__typename": "PullRequest",
                            "number": 42,
                            "title": "Test PR",
                            "headRefName": "feature-branch",
                            "baseRefName": "main",
                            "updatedAt": recent_date,
                            "url": "https://github.com/org/repo/pull/42",
                            "author": {"login": "testuser"},
                            "headRefOid": "abc123",
                            "state": "OPEN",
                            "isDraft": False,
                            "repository": {
                                "name": "repo",
                                "nameWithOwner": "org/repo"
                            }
                        }
                    ],
                    "pageInfo": {
                        "hasNextPage": False,
                        "endCursor": None
                    }
                }
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.post", return_value=mock_response):
            prs = monitor.discover_open_prs(cutoff_hours=24)
            
            assert len(prs) == 1
            assert prs[0]["number"] == 42
            assert prs[0]["title"] == "Test PR"

    def test_discover_open_prs_no_token(self, monkeypatch):
        """Test discover_open_prs raises error when no token available."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: None
        )
        
        with pytest.raises(RuntimeError, match="No GitHub token available"):
            monitor.discover_open_prs(cutoff_hours=24)

    def test_discover_open_prs_api_error(self, monkeypatch):
        """Test discover_open_prs handles API errors gracefully."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.HTTPError("API Error")
        http_error.response = mock_response
        mock_response.raise_for_status = Mock(side_effect=http_error)
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="GraphQL search failed"):
                monitor.discover_open_prs(cutoff_hours=24)

    def test_discover_open_prs_pagination(self, monkeypatch):
        """Test discover_open_prs handles pagination correctly."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # First page response
        first_response = Mock()
        first_response.status_code = 200
        from datetime import datetime, timedelta, timezone
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        first_response.json.return_value = {
            "data": {
                "search": {
                    "nodes": [
                        {
                            "__typename": "PullRequest",
                            "number": 1,
                            "title": "PR 1",
                            "headRefName": "branch1",
                            "baseRefName": "main",
                            "updatedAt": recent_date,
                            "url": "https://github.com/org/repo/pull/1",
                            "author": {"login": "user1"},
                            "headRefOid": "abc123",
                            "state": "OPEN",
                            "isDraft": False,
                            "repository": {"name": "repo", "nameWithOwner": "org/repo"}
                        }
                    ],
                    "pageInfo": {
                        "hasNextPage": True,
                        "endCursor": "cursor123"
                    }
                }
            }
        }
        first_response.raise_for_status = Mock()
        
        # Second page response
        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "data": {
                "search": {
                    "nodes": [
                        {
                            "__typename": "PullRequest",
                            "number": 2,
                            "title": "PR 2",
                            "headRefName": "branch2",
                            "baseRefName": "main",
                            "updatedAt": recent_date,
                            "url": "https://github.com/org/repo/pull/2",
                            "author": {"login": "user2"},
                            "headRefOid": "def456",
                            "state": "OPEN",
                            "isDraft": False,
                            "repository": {"name": "repo", "nameWithOwner": "org/repo"}
                        }
                    ],
                    "pageInfo": {
                        "hasNextPage": False,
                        "endCursor": None
                    }
                }
            }
        }
        second_response.raise_for_status = Mock()
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.post", side_effect=[first_response, second_response]):
            prs = monitor.discover_open_prs(cutoff_hours=24)
            
            assert len(prs) == 2
            assert prs[0]["number"] == 1
            assert prs[1]["number"] == 2


class TestGitHubAPIPagination:
    """Test suite for GitHub API pagination in comment fetching."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def monitor(self, temp_data_dir):
        """Create monitor instance for testing."""
        return JleechanorgPRMonitor(
            log_dir=str(temp_data_dir),
        )

    def test_red_get_pr_comment_state_fetches_all_pages(self, monitor, monkeypatch):
        """
        🔴 RED TEST: _get_pr_comment_state() should fetch ALL comment pages, not just first 100.

        Given: PR with 356 comments (requires 4 pages at per_page=100)
        When: Calling _get_pr_comment_state()
        Then: Should return all 356 comments, not just first 100

        Current behavior: Returns only first 100 comments
        Expected behavior: Returns all 356 comments via pagination
        """
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123",
        )
        # Mock requests to simulate paginated response
        mock_response_page1 = MagicMock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = [{"id": i, "body": f"Comment {i}"} for i in range(100)]
        mock_response_page1.headers = {
            "Link": '<https://api.github.com/repos/jleechanorg/worldarchitect.ai/issues/3096/comments?page=2&per_page=100>; rel="next"'
        }

        mock_response_page2 = MagicMock()
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = [{"id": i, "body": f"Comment {i}"} for i in range(100, 200)]
        mock_response_page2.headers = {
            "Link": '<https://api.github.com/repos/jleechanorg/worldarchitect.ai/issues/3096/comments?page=3&per_page=100>; rel="next"'
        }

        mock_response_page3 = MagicMock()
        mock_response_page3.status_code = 200
        mock_response_page3.json.return_value = [{"id": i, "body": f"Comment {i}"} for i in range(200, 300)]
        mock_response_page3.headers = {
            "Link": '<https://api.github.com/repos/jleechanorg/worldarchitect.ai/issues/3096/comments?page=4&per_page=100>; rel="next"'
        }

        mock_response_page4 = MagicMock()
        mock_response_page4.status_code = 200
        mock_response_page4.json.return_value = [{"id": i, "body": f"Comment {i}"} for i in range(300, 356)]
        mock_response_page4.headers = {}  # No next link = last page

        mock_pr_response = MagicMock()
        mock_pr_response.status_code = 200
        mock_pr_response.json.return_value = {"head": {"sha": "abc123"}}

        with patch(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.get"
        ) as mock_get:
            # First call = PR data, subsequent calls = comment pages
            mock_get.side_effect = [
                mock_pr_response,
                mock_response_page1,
                mock_response_page2,
                mock_response_page3,
                mock_response_page4,
            ]

            head_sha, comments = monitor._get_pr_comment_state("jleechanorg/worldarchitect.ai", 3096)

            # Verify head SHA
            assert head_sha == "abc123", "Should extract head SHA from PR data"

            assert comments is not None, "Should return comments list, not None"
            assert len(comments) == 356, (
                f"Should fetch ALL 356 comments across 4 pages, got {len(comments)}\n"
                f"Current implementation only fetches first page (per_page=100)\n"
                f"Need to implement pagination following Link headers"
            )

            # Verify all comments present
            comment_ids = [c["id"] for c in comments]
            assert comment_ids == list(range(356)), "Should include all comment IDs from all pages"

    def test_red_pagination_handles_empty_pr(self, monitor, monkeypatch):
        """
        🔴 RED TEST: Pagination should handle PRs with 0 comments correctly.

        Given: PR with no comments
        When: Calling _get_pr_comment_state()
        Then: Should return empty list, not fail
        """
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123",
        )
        mock_pr_response = MagicMock()
        mock_pr_response.status_code = 200
        mock_pr_response.json.return_value = {"head": {"sha": "def456"}}

        mock_comments_response = MagicMock()
        mock_comments_response.status_code = 200
        mock_comments_response.json.return_value = []
        mock_comments_response.headers = {}  # No Link header

        with patch(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.get"
        ) as mock_get:
            mock_get.side_effect = [mock_pr_response, mock_comments_response]

            head_sha, comments = monitor._get_pr_comment_state("jleechanorg/worldarchitect.ai", 999)

            assert head_sha == "def456"
            assert comments == [], "Empty PR should return empty list"

    def test_red_pagination_handles_single_page(self, monitor, monkeypatch):
        """
        🔴 RED TEST: Pagination should work for PRs with <100 comments (single page).

        Given: PR with 30 comments (single page)
        When: Calling _get_pr_comment_state()
        Then: Should return all 30 comments without trying to paginate
        """
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123",
        )
        mock_pr_response = MagicMock()
        mock_pr_response.status_code = 200
        mock_pr_response.json.return_value = {"head": {"sha": "ghi789"}}

        mock_comments_response = MagicMock()
        mock_comments_response.status_code = 200
        mock_comments_response.json.return_value = [{"id": i, "body": f"Comment {i}"} for i in range(30)]
        mock_comments_response.headers = {}  # No Link header (single page)

        with patch(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.get"
        ) as mock_get:
            mock_get.side_effect = [mock_pr_response, mock_comments_response]

            head_sha, comments = monitor._get_pr_comment_state("jleechanorg/worldarchitect.ai", 4288)

            assert head_sha == "ghi789"
            assert len(comments) == 30, "Should return all comments from single page"


class TestGetFixCommentWatchStateWithRequests:
    """Test _get_fix_comment_watch_state() using Python requests instead of gh CLI."""

    def test_get_fix_comment_watch_state_success(self, monkeypatch):
        """Test _get_fix_comment_watch_state successfully fetches PR data via REST API."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        # Mock get_github_token
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock PR data response
        pr_response = Mock()
        pr_response.status_code = 200
        pr_response.json.return_value = {
            "head": {"sha": "abc123", "ref": "feature-branch"},
            "title": "Test PR",
            "user": {"login": "testuser"}
        }
        pr_response.raise_for_status = Mock()
        
        # Mock comments response
        comments_response = Mock()
        comments_response.status_code = 200
        comments_response.json.return_value = [
            {"id": 1, "body": "Comment 1"},
            {"id": 2, "body": "Comment 2"}
        ]
        comments_response.raise_for_status = Mock()
        
        # Mock commits response (with messageHeadline structure)
        commits_response = Mock()
        commits_response.status_code = 200
        commits_response.json.return_value = [
            {"sha": "abc123", "commit": {"message": "Test commit", "messageHeadline": "Test commit"}}
        ]
        commits_response.raise_for_status = Mock()
        
        get_calls = []
        def mock_get(url, headers=None, timeout=None, params=None):
            get_calls.append(url)
            if "pulls" in url and "comments" not in url and "commits" not in url:
                return pr_response
            elif "comments" in url:
                return comments_response
            elif "commits" in url:
                return commits_response
            return Mock(status_code=200, json=lambda: {}, raise_for_status=Mock())
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.get", side_effect=mock_get):
            pr_data, head_sha, comments, headlines = monitor._get_fix_comment_watch_state("org/repo", 123)
            
            assert head_sha == "abc123"
            assert pr_data["title"] == "Test PR"
            assert len(comments) == 2
            assert isinstance(headlines, list)  # headlines is a list of commit message headlines
            # Verify all three endpoints were called
            assert any("pulls/123" in url and "comments" not in url and "commits" not in url for url in get_calls)
            assert any("issues/123/comments" in url for url in get_calls)
            assert any("pulls/123/commits" in url for url in get_calls)

    def test_get_fix_comment_watch_state_no_token(self, monkeypatch):
        """Test _get_fix_comment_watch_state raises error when no token available."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: None
        )
        
        with pytest.raises(RuntimeError, match="No GitHub token available"):
            monitor._get_fix_comment_watch_state("org/repo", 123)

    def test_get_fix_comment_watch_state_api_error(self, monkeypatch):
        """Test _get_fix_comment_watch_state handles API errors gracefully."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.HTTPError("Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status = Mock(side_effect=http_error)
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.get", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to fetch PR data"):
                monitor._get_fix_comment_watch_state("org/repo", 123)

    def test_get_fix_comment_watch_state_comments_optional(self, monkeypatch):
        """Test _get_fix_comment_watch_state handles missing comments gracefully."""
        monitor = JleechanorgPRMonitor(automation_username="test-user")
        
        monkeypatch.setattr(
            "automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.get_github_token",
            lambda: "test-token-123"
        )
        
        # Mock PR data response
        pr_response = Mock()
        pr_response.status_code = 200
        pr_response.json.return_value = {
            "head": {"sha": "abc123", "ref": "feature-branch"},
            "title": "Test PR",
            "user": {"login": "testuser"}
        }
        pr_response.raise_for_status = Mock()
        
        # Mock comments error (optional)
        comments_error = requests.RequestException("Network error")
        
        # Mock commits response
        commits_response = Mock()
        commits_response.status_code = 200
        commits_response.json.return_value = []
        commits_response.raise_for_status = Mock()
        
        call_count = 0
        def mock_get(url, headers=None, timeout=None, params=None):
            nonlocal call_count
            call_count += 1
            if "pulls" in url and "comments" not in url and "commits" not in url:
                return pr_response
            elif "comments" in url:
                raise comments_error  # Comments fail but should be handled
            elif "commits" in url:
                return commits_response
            return Mock(status_code=200, json=lambda: {}, raise_for_status=Mock())
        
        with patch("automation.jleechanorg_pr_automation.jleechanorg_pr_monitor.requests.get", side_effect=mock_get):
            pr_data, head_sha, comments, headlines = monitor._get_fix_comment_watch_state("org/repo", 123)
            
            # Should still succeed with empty comments list
            assert head_sha == "abc123"
            assert comments == []  # Empty list when comments fail
            assert isinstance(headlines, list)  # headlines is a list
