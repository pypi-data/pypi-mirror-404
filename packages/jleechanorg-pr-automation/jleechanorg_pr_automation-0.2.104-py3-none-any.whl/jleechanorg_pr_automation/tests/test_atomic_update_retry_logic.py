#!/usr/bin/env python3
"""
🔴 RED TEST: Retry logic for atomic_update() failures

PROBLEM:
When atomic_update() fails due to transient file I/O errors (file lock contention,
temporary disk I/O issues), try_process_pr() immediately rejects the request.
This causes false rejections for valid PRs during transient failures.

SOLUTION:
Implement retry logic with exponential backoff:
- Retry atomic_update() up to 3 times
- Exponential backoff: 50ms, 100ms, 200ms
- Only return False after all retries exhausted
- If any retry succeeds, return True

This improves availability while maintaining concurrent safety.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, call

import pytest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.utils import SafeJSONManager


class TestAtomicUpdateRetryLogic:
    """Test suite for atomic_update() retry logic."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for safety manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize empty files
            SafeJSONManager().write_json(str(Path(tmpdir) / "pr_attempts.json"), {})
            SafeJSONManager().write_json(str(Path(tmpdir) / "pr_inflight.json"), {})
            SafeJSONManager().write_json(str(Path(tmpdir) / "global_runs.json"), {})
            yield Path(tmpdir)

    def test_try_process_pr_retries_on_transient_failure(self, temp_data_dir):
        """
        🔴 RED TEST: Verify atomic_update() is retried on transient failures.

        Given: atomic_update() fails twice, succeeds on third attempt
        When: try_process_pr() is called
        Then: Should retry and eventually return True (availability improved)

        This test will FAIL initially because retry logic doesn't exist yet.
        """
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

        pr_number = 3185
        repo = "test-repo"
        branch = "test-branch"

        # Mock atomic_update to fail twice, succeed on third attempt
        # We need to call the callback to set the success variable
        call_count = [0]

        def mock_atomic_with_callback(file_path, update_func, default=None):
            call_count[0] += 1
            # Call the callback to set internal state
            update_func(default if default is not None else {})
            # Return False for first 2 calls, True for 3rd
            return call_count[0] >= 3

        with patch('jleechanorg_pr_automation.utils.json_manager.atomic_update', side_effect=mock_atomic_with_callback):
            start_time = time.time()
            result = manager.try_process_pr(pr_number, repo, branch)
            elapsed = time.time() - start_time

            # Verify retry happened
            assert call_count[0] == 3, (
                f"Expected 3 atomic_update() calls (initial + 2 retries), got {call_count[0]}"
            )

            # Verify exponential backoff (should take at least 50ms + 100ms = 150ms)
            assert elapsed >= 0.15, (
                f"Expected exponential backoff delays (50ms + 100ms), elapsed: {elapsed*1000:.1f}ms"
            )

            # Verify success after retry
            assert result is True, (
                f"Expected True after successful retry, got {result}"
            )

            print(f"\n✅ RETRY LOGIC TEST:")
            print(f"   atomic_update() calls: {call_count[0]}")
            print(f"   Result: {result}")
            print(f"   Elapsed: {elapsed*1000:.1f}ms")

    def test_try_process_pr_fails_after_max_retries(self, temp_data_dir):
        """
        🔴 RED TEST: Verify failure after all retries exhausted.

        Given: atomic_update() fails on all 3 attempts
        When: try_process_pr() is called
        Then: Should return False (cannot guarantee concurrent safety)

        This maintains correctness - if persistent failure, reject request.
        """
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

        pr_number = 3664
        repo = "test-repo"
        branch = "test-branch"

        # Mock atomic_update to always fail
        call_count = [0]

        def mock_atomic_always_fail(file_path, update_func, default=None):
            call_count[0] += 1
            # Call callback but return False (write failed)
            update_func(default if default is not None else {})
            return False

        with patch('jleechanorg_pr_automation.utils.json_manager.atomic_update', side_effect=mock_atomic_always_fail):
            result = manager.try_process_pr(pr_number, repo, branch)

            # Verify all retries attempted
            assert call_count[0] == 3, (
                f"Expected 3 atomic_update() calls, got {call_count[0]}"
            )

            # Verify failure after exhausting retries
            assert result is False, (
                f"Expected False after all retries failed, got {result}"
            )

            print(f"\n✅ MAX RETRIES TEST:")
            print(f"   atomic_update() calls: {call_count[0]}")
            print(f"   Result: {result} (correctly rejected after retries)")

    def test_try_process_pr_succeeds_immediately(self, temp_data_dir):
        """
        ✅ GREEN TEST: Verify no retry on immediate success.

        Given: atomic_update() succeeds on first attempt
        When: try_process_pr() is called
        Then: Should return True immediately without retries
        """
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

        pr_number = 3096
        repo = "test-repo"
        branch = "test-branch"

        # No mocking - use real atomic_update which should succeed
        start_time = time.time()
        result = manager.try_process_pr(pr_number, repo, branch)
        elapsed = time.time() - start_time

        # Verify fast completion (no backoff delays)
        assert elapsed < 0.2, (
            f"Expected fast completion (<200ms), elapsed: {elapsed*1000:.1f}ms"
        )

        # Verify success
        assert result is True, (
            f"Expected True on immediate success, got {result}"
        )

        print(f"\n✅ IMMEDIATE SUCCESS TEST:")
        print(f"   Result: {result}")
        print(f"   Elapsed: {elapsed*1000:.1f}ms (no retry needed)")

    def test_release_pr_slot_retries_on_failure(self, temp_data_dir):
        """
        🔴 RED TEST: Verify release_pr_slot() retries to prevent slot leaks.

        Given: atomic_update() fails twice, succeeds on third attempt
        When: release_pr_slot() is called
        Then: Should retry and eventually succeed (prevent slot leak)

        SLOT LEAK RISK: If release fails, inflight count stuck at 1, blocking all future processing.
        """
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

        # First reserve a slot
        pr_number = 4001
        repo = "test-repo"
        branch = "test-branch"

        # Use real atomic_update for reservation
        success = manager.try_process_pr(pr_number, repo, branch)
        assert success is True, "Should successfully reserve slot"

        # Verify slot reserved
        pr_key = manager._make_pr_key(pr_number, repo, branch)
        assert manager._pr_inflight_cache.get(pr_key, 0) == 1

        # Now test release with retry
        call_count = [0]

        def mock_atomic_with_callback(file_path, update_func, default=None):
            call_count[0] += 1
            # Call callback to update internal state
            update_func(default if default is not None else {})
            # Fail twice, succeed on third
            return call_count[0] >= 3

        with patch('jleechanorg_pr_automation.utils.json_manager.atomic_update', side_effect=mock_atomic_with_callback):
            manager.release_pr_slot(pr_number, repo, branch)

            # Verify retry happened
            assert call_count[0] == 3, (
                f"Expected 3 atomic_update() calls for release retry, got {call_count[0]}"
            )

            print(f"\n✅ RELEASE RETRY TEST:")
            print(f"   atomic_update() calls: {call_count[0]}")
            print(f"   Slot leak prevented: retry succeeded")

    def test_release_pr_slot_logs_error_after_max_retries(self, temp_data_dir):
        """
        🔴 RED TEST: Verify release_pr_slot() logs error if all retries fail.

        Given: atomic_update() fails on all attempts
        When: release_pr_slot() is called
        Then: Should log error (manual intervention needed for slot leak)

        NOTE: Slot leak is acceptable here because:
        1. It's rare (persistent I/O failure)
        2. Better than crashing/raising exception
        3. Operators can manually clear pr_inflight.json
        """
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

        # First reserve a slot
        pr_number = 4002
        repo = "test-repo"
        branch = "test-branch"
        success = manager.try_process_pr(pr_number, repo, branch)
        assert success is True

        # Test release failure
        call_count = [0]

        def mock_atomic_always_fail(file_path, update_func, default=None):
            call_count[0] += 1
            # Call callback but always fail write
            update_func(default if default is not None else {})
            return False

        with patch('jleechanorg_pr_automation.utils.json_manager.atomic_update', side_effect=mock_atomic_always_fail):
            # Use caplog to capture log messages
            with patch.object(manager.logger, 'error') as mock_log_error:
                manager.release_pr_slot(pr_number, repo, branch)

                # Verify all retries attempted
                assert call_count[0] == 3, (
                    f"Expected 3 atomic_update() calls, got {call_count[0]}"
                )

                # Verify error logged
                assert mock_log_error.call_count > 0, "Should log error after all retries failed"

                print(f"\n✅ RELEASE FAILURE TEST:")
                print(f"   atomic_update() calls: {call_count[0]}")
                print(f"   Error logged: {mock_log_error.call_count} times")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
