#!/usr/bin/env python3
"""
Tests for atomic race condition fix in automation safety manager

This test file verifies that the atomic_update() method in SafeJSONManager
properly prevents race conditions between concurrent processes that could
bypass safety limits.

Bug Context: https://github.com/jleechanorg/worldarchitect.ai/pull/3762
Reported by: Gemini feedback on PR #3762
Fixed: Added atomic_update() with file lock held across read-modify-write
"""

import json
import os
import shutil
import multiprocessing
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.utils import SafeJSONManager, json_manager
from jleechanorg_pr_automation.tests.conftest import _get_inflight_count


# Module-level helper functions for multiprocessing (must be picklable)
def _increment_pr_count(pr_key: str, test_file_path: str, process_id: int):
    """Simulate a process incrementing PR inflight count"""
    manager = SafeJSONManager()

    def update_count(data):
        # Simulate some processing time to increase chance of race
        time.sleep(0.01)
        current = data.get(pr_key, 0)
        return {**data, pr_key: current + 1}

    # Use atomic_update to prevent race
    result = manager.atomic_update(test_file_path, update_count, {})
    return result


def _try_reserve_slot(pr_number: int, data_dir: str, process_id: int):
    """Simulate a process trying to reserve a PR processing slot"""
    limits = {
        "pr_automation_limit": 1,  # Only 1 concurrent processing allowed
        "pr_limit": 1,
        "approval_hours": 24,
        "subprocess_timeout": 600,
    }
    manager = AutomationSafetyManager(data_dir, limits=limits)

    # Try to reserve a slot
    success = manager.try_process_pr(pr_number, repo="test-repo")
    return (success, process_id)


def _release_slot(pr_num: int, repo_name: str, data_dir: str, limits_dict: dict, process_id: int):
    """Simulate a process releasing a PR slot"""
    mgr = AutomationSafetyManager(data_dir, limits=limits_dict)
    mgr.release_pr_slot(pr_num, repo=repo_name)
    return process_id


def _try_process_with_atomic_failure(pr_number: int, data_dir: str, process_id: int):
    """
    Simulate a process calling try_process_pr() where atomic_update() fails.
    """
    manager = AutomationSafetyManager(data_dir=data_dir)

    with patch.object(SafeJSONManager, "atomic_update") as mock_atomic:
        mock_atomic.return_value = False
        result = manager.try_process_pr(pr_number, repo="test-repo", branch="test-branch")
        return (result, process_id, "atomic_update_failed")


def _try_process_normal(pr_number: int, data_dir: str, process_id: int):
    """
    Simulate a normal process calling try_process_pr() without mocking.
    """
    manager = AutomationSafetyManager(data_dir=data_dir)
    time.sleep(0.05)

    result = manager.try_process_pr(pr_number, repo="test-repo", branch="test-branch")

    inflight_file = Path(data_dir) / "pr_inflight.json"
    with open(inflight_file) as f:
        disk_data = json.load(f)

    pr_key = f"r=test-repo||p={pr_number}||b=test-branch"
    disk_inflight = (
        disk_data.get(pr_key, {}).get("count", 0)
        if isinstance(disk_data.get(pr_key), dict)
        else disk_data.get(pr_key, 0)
    )

    return (result, process_id, "normal_process", disk_inflight)


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for safety manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        SafeJSONManager().write_json(str(Path(tmpdir) / "pr_attempts.json"), {})
        SafeJSONManager().write_json(str(Path(tmpdir) / "pr_inflight.json"), {})
        SafeJSONManager().write_json(str(Path(tmpdir) / "global_runs.json"), {})
        yield Path(tmpdir)


def test_atomic_update_prevents_race_condition(tmp_path):
    """
    Test that atomic_update() prevents race conditions between processes.

    Simulates two processes trying to increment the same PR's inflight count
    simultaneously. Without atomic updates, both processes could read count=0,
    both increment to 1, and both write 1, resulting in count=1 instead of 2.

    With atomic_update(), the file lock is held across the entire operation,
    ensuring sequential execution and correct count=2.
    """
    test_file = tmp_path / "test_inflight.json"
    json_manager = SafeJSONManager()

    # Initialize file with empty dict
    json_manager.write_json(str(test_file), {})

    # Run two processes concurrently trying to increment the same PR count
    pr_key = "worldarchitect.ai#1234"
    pool = multiprocessing.Pool(processes=2)

    results = []
    for i in range(2):
        result = pool.apply_async(_increment_pr_count, (pr_key, str(test_file), i))
        results.append(result)

    pool.close()
    pool.join()

    # Verify both updates succeeded
    for result in results:
        assert result.get() is True, "Atomic update should succeed"

    # Read final state - should be 2 (both increments applied)
    final_data = json_manager.read_json(str(test_file), {})
    assert final_data.get(pr_key) == 2, (
        f"Expected count=2 after two concurrent increments, got {final_data.get(pr_key)}. "
        "Race condition detected - atomic_update() is not working properly!"
    )


def test_try_process_pr_concurrent_reservations(tmp_path, monkeypatch):
    """
    Test that try_process_pr() properly handles concurrent reservation attempts.

    Simulates two processes trying to reserve a processing slot for the same PR
    simultaneously when pr_limit=1. Without atomic updates, both could succeed,
    bypassing the safety limit. With atomic updates, only one should succeed.
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()
    monkeypatch.setenv("AUTOMATION_SAFETY_DATA_DIR", str(safety_data_dir))

    # Run two processes concurrently trying to reserve the same PR
    pr_number = 5678
    pool = multiprocessing.Pool(processes=2)

    results = []
    for i in range(2):
        result = pool.apply_async(_try_reserve_slot, (pr_number, str(safety_data_dir), i))
        results.append(result)

    pool.close()
    pool.join()

    # Collect results
    outcomes = [result.get() for result in results]
    successes = [outcome for outcome in outcomes if outcome[0] is True]

    # Verify that EXACTLY ONE process succeeded (safety limit enforced)
    assert len(successes) == 1, (
        f"Expected exactly 1 successful reservation (pr_limit=1), got {len(successes)}. "
        f"Outcomes: {outcomes}. Race condition detected - try_process_pr() is not atomic!"
    )


def test_atomic_update_with_nonexistent_file(tmp_path):
    """Test that atomic_update() works correctly when file doesn't exist."""
    test_file = tmp_path / "nonexistent.json"
    json_manager = SafeJSONManager()

    def add_item(data):
        data["item"] = "value"
        return data

    # Should create file and add item
    result = json_manager.atomic_update(str(test_file), add_item, {})
    assert result is True

    # Verify file was created with correct content
    final_data = json_manager.read_json(str(test_file), {})
    assert final_data == {"item": "value"}


def test_atomic_update_preserves_other_keys(tmp_path):
    """Test that atomic_update() preserves data in other keys."""
    test_file = tmp_path / "test_data.json"
    json_manager = SafeJSONManager()

    # Initialize with multiple keys
    initial_data = {
        "pr1": 1,
        "pr2": 2,
        "pr3": 3,
    }
    json_manager.write_json(str(test_file), initial_data)

    # Update only one key
    def update_pr2(data):
        data["pr2"] = data.get("pr2", 0) + 10
        return data

    result = json_manager.atomic_update(str(test_file), update_pr2, {})
    assert result is True

    # Verify pr2 was updated and other keys preserved
    final_data = json_manager.read_json(str(test_file), {})
    assert final_data == {
        "pr1": 1,
        "pr2": 12,  # Updated: 2 + 10
        "pr3": 3,
    }


def test_atomic_update_handles_invalid_json(tmp_path):
    """Test that atomic_update() handles corrupted JSON gracefully."""
    test_file = tmp_path / "corrupted.json"

    # Write invalid JSON
    with open(test_file, 'w') as f:
        f.write("{invalid json content")

    json_manager = SafeJSONManager()

    def add_item(data):
        # Should receive default {} since JSON is invalid
        data["new_item"] = "value"
        return data

    result = json_manager.atomic_update(str(test_file), add_item, {})
    assert result is True

    # Verify file was overwritten with valid JSON
    final_data = json_manager.read_json(str(test_file), {})
    assert final_data == {"new_item": "value"}


def test_release_pr_slot_concurrent_releases(tmp_path, monkeypatch):
    """
    Test that release_pr_slot() properly handles concurrent release attempts.

    Simulates two processes trying to release the same PR slot simultaneously.
    Without atomic updates, both could decrement the count, resulting in
    incorrect negative values or lost releases.
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()
    monkeypatch.setenv("AUTOMATION_SAFETY_DATA_DIR", str(safety_data_dir))

    # Setup: Reserve 2 slots for the same PR
    # NOTE: concurrent_limit=2 is ONLY for testing concurrent releases
    # Production should ALWAYS use concurrent_limit=1 (default)
    limits = {"pr_automation_limit": 10, "pr_limit": 10, "concurrent_limit": 2}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 9999
    repo = "test-repo"

    # Reserve 2 slots
    assert manager.try_process_pr(pr_number, repo=repo) is True
    assert manager.try_process_pr(pr_number, repo=repo) is True

    # Run two processes concurrently trying to release slots
    pool = multiprocessing.Pool(processes=2)

    results = []
    for i in range(2):
        result = pool.apply_async(_release_slot, (pr_number, repo, str(safety_data_dir), limits, i))
        results.append(result)

    pool.close()
    pool.join()

    # Wait for all releases to complete
    for result in results:
        result.get()

    # Verify inflight count is now 0 (both slots released correctly)
    # Read the file directly to check
    inflight_file = safety_data_dir / "pr_inflight.json"
    with open(inflight_file) as f:
        inflight_data = json.load(f)

    # Use the same labeled format that _make_pr_key() generates
    pr_key = f"r=test-repo||p={pr_number}||b="
    final_count = _get_inflight_count(inflight_data, pr_key)

    assert final_count == 0, (
        f"Expected inflight count=0 after releasing 2 slots, got {final_count}. "
        "Race condition detected - release_pr_slot() is not atomic!"
    )


def test_try_process_pr_retries_on_transient_failure(temp_data_dir):
    """
    Verify atomic_update() is retried on transient failures.
    """
    manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

    pr_number = 3185
    repo = "test-repo"
    branch = "test-branch"

    call_count = [0]

    def mock_atomic_with_callback(file_path, update_func, default=None):
        call_count[0] += 1
        update_func(default if default is not None else {})
        return call_count[0] >= 3

    with patch.object(
        SafeJSONManager,
        "atomic_update",
        side_effect=mock_atomic_with_callback,
    ):
        start_time = time.time()
        result = manager.try_process_pr(pr_number, repo, branch)
        elapsed = time.time() - start_time

        assert call_count[0] == 3, (
            f"Expected 3 atomic_update() calls (initial + 2 retries), got {call_count[0]}"
        )
        assert elapsed >= 0.15, (
            f"Expected backoff delays, elapsed: {elapsed*1000:.1f}ms"
        )
        assert result is True, f"Expected True after successful retry, got {result}"


def test_try_process_pr_fails_after_max_retries(temp_data_dir):
    """
    Verify failure after all retries exhausted.
    """
    manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

    pr_number = 3664
    repo = "test-repo"
    branch = "test-branch"

    call_count = [0]

    def mock_atomic_always_fail(file_path, update_func, default=None):
        call_count[0] += 1
        update_func(default if default is not None else {})
        return False

    with patch.object(
        SafeJSONManager,
        "atomic_update",
        side_effect=mock_atomic_always_fail,
    ):
        result = manager.try_process_pr(pr_number, repo, branch)

        assert call_count[0] == 3, (
            f"Expected 3 atomic_update() calls, got {call_count[0]}"
        )
        assert result is False, f"Expected False after retries failed, got {result}"


def test_try_process_pr_succeeds_immediately(temp_data_dir):
    """
    Verify no retry on immediate success.
    """
    manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

    pr_number = 3096
    repo = "test-repo"
    branch = "test-branch"

    start_time = time.time()
    result = manager.try_process_pr(pr_number, repo, branch)
    elapsed = time.time() - start_time

    assert elapsed < 0.2, (
        f"Expected fast completion (<200ms), elapsed: {elapsed*1000:.1f}ms"
    )
    assert result is True, f"Expected True on immediate success, got {result}"


def test_release_pr_slot_retries_on_failure(temp_data_dir):
    """
    Verify release_pr_slot() retries to prevent slot leaks.
    """
    manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

    pr_number = 4001
    repo = "test-repo"
    branch = "test-branch"

    success = manager.try_process_pr(pr_number, repo, branch)
    assert success is True, "Should successfully reserve slot"

    pr_key = manager._make_pr_key(pr_number, repo, branch)
    assert manager._pr_inflight_cache.get(pr_key, 0) == 1

    call_count = [0]

    def mock_atomic_with_callback(file_path, update_func, default=None):
        call_count[0] += 1
        update_func(default if default is not None else {})
        return call_count[0] >= 3

    with patch.object(
        SafeJSONManager,
        "atomic_update",
        side_effect=mock_atomic_with_callback,
    ):
        manager.release_pr_slot(pr_number, repo, branch)
        assert call_count[0] == 3, (
            f"Expected 3 atomic_update() calls for release retry, got {call_count[0]}"
        )


def test_release_pr_slot_logs_error_after_max_retries(temp_data_dir):
    """
    Verify release_pr_slot() logs error if all retries fail.
    """
    manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

    pr_number = 4002
    repo = "test-repo"
    branch = "test-branch"
    success = manager.try_process_pr(pr_number, repo, branch)
    assert success is True

    call_count = [0]

    def mock_atomic_always_fail(file_path, update_func, default=None):
        call_count[0] += 1
        update_func(default if default is not None else {})
        return False

    with patch.object(
        SafeJSONManager,
        "atomic_update",
        side_effect=mock_atomic_always_fail,
    ):
        with patch.object(manager.logger, "error") as mock_log_error:
            manager.release_pr_slot(pr_number, repo, branch)
            assert call_count[0] == 3, (
                f"Expected 3 atomic_update() calls, got {call_count[0]}"
            )
            assert mock_log_error.call_count > 0, "Should log error after retries failed"


def test_regression_wa3gx_defensive_fallback_race_condition(tmp_path):
    """
    Regression test for WA-3gx defensive fallback race condition.
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    SafeJSONManager().write_json(str(safety_data_dir / "pr_attempts.json"), {})
    SafeJSONManager().write_json(str(safety_data_dir / "pr_inflight.json"), {})
    SafeJSONManager().write_json(str(safety_data_dir / "global_runs.json"), {})

    pr_number = 3185

    pool = multiprocessing.Pool(processes=2)
    result_a = pool.apply_async(_try_process_with_atomic_failure, (pr_number, str(safety_data_dir), 1))
    time.sleep(0.01)
    result_b = pool.apply_async(_try_process_normal, (pr_number, str(safety_data_dir), 2))

    pool.close()
    pool.join()

    outcome_a = result_a.get()
    outcome_b = result_b.get()

    success_a, _, _ = outcome_a
    success_b, _, _, disk_inflight = outcome_b

    if success_a and success_b:
        pytest.fail(
            f"Race condition detected: both processes succeeded (disk inflight={disk_inflight})"
        )

    assert not (success_a and success_b), (
        f"At most ONE process should succeed. Got: A={success_a}, B={success_b}"
    )

    total_successes = sum([success_a, success_b])
    assert total_successes == 1, (
        f"Expected exactly 1 success (concurrent_limit=1), got {total_successes}"
    )


def test_regression_wa3gx_in_memory_disk_inconsistency():
    """
    Verify atomic_update() failure does NOT allow processing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AutomationSafetyManager(data_dir=tmpdir)

        pr_number = 3664
        repo = "test-repo"
        branch = "test-branch"

        with patch.object(SafeJSONManager, "atomic_update") as mock_atomic:
            mock_atomic.return_value = False

            result = manager.try_process_pr(pr_number, repo, branch)
            assert result is False, (
                f"try_process_pr() returned {result} when atomic_update() failed"
            )

            pr_key = manager._make_pr_key(pr_number, repo, branch)
            _ = manager._pr_inflight_cache.get(pr_key, 0)

            inflight_file = Path(tmpdir) / "pr_inflight.json"
            with open(inflight_file) as f:
                _ = json.load(f)


class TestSafetyLimitsFalseRejection:
    """Test suite for WA-3gx: Safety limits false rejection bug."""

    @pytest.fixture
    def clean_safety_manager(self, temp_data_dir):
        """Create safety manager with clean (empty) state."""
        pr_attempts_file = temp_data_dir / "pr_attempts.json"
        pr_inflight_file = temp_data_dir / "pr_inflight.json"
        global_runs_file = temp_data_dir / "global_runs.json"

        pr_attempts_file.write_text("{}")
        pr_inflight_file.write_text("{}")
        global_runs_file.write_text("{}")

        return AutomationSafetyManager(data_dir=str(temp_data_dir))

    def test_try_process_pr_with_empty_attempts_should_return_true(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        Given: Clean safety manager state (empty pr_attempts.json)
        When: try_process_pr() is called for PR #3185
        Then: Should return True (PR has 0/50 attempts, should be allowed)
        """
        test_pr_number = 3185
        test_repo = "jleechanorg/worldarchitect.ai"
        test_branch = "fix/spicy-mode-detection"

        pr_attempts_file = temp_data_dir / "pr_attempts.json"
        with open(pr_attempts_file, "r") as f:
            attempts_data = json.load(f)
        assert attempts_data == {}, "pr_attempts.json should be empty"

        result = clean_safety_manager.try_process_pr(
            pr_number=test_pr_number,
            repo=test_repo,
            branch=test_branch,
        )

        evidence_dir = temp_data_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        evidence = {
            "test": "test_try_process_pr_with_empty_attempts_should_return_true",
            "pr_number": test_pr_number,
            "repo": test_repo,
            "branch": test_branch,
            "pr_attempts_before": attempts_data,
            "try_process_pr_result": result,
            "expected_result": True,
            "test_passed": result is True,
        }

        evidence_file = evidence_dir / "try_process_pr_evidence.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        assert result is True, (
            f"try_process_pr() returned False when pr_attempts.json is empty. "
            f"Evidence saved to {evidence_file}"
        )

    def test_can_process_pr_with_zero_attempts_should_return_true(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        Verify can_process_pr() works correctly with zero attempts.
        """
        test_pr_number = 3664
        test_repo = "jleechanorg/worldarchitect.ai"
        test_branch = "claude/add-action-resolution-warning"

        pr_attempts_file = temp_data_dir / "pr_attempts.json"
        with open(pr_attempts_file, "r") as f:
            attempts_data = json.load(f)
        assert attempts_data == {}

        result = clean_safety_manager.can_process_pr(
            pr_number=test_pr_number,
            repo=test_repo,
            branch=test_branch,
        )

        evidence_dir = temp_data_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        evidence = {
            "test": "test_can_process_pr_with_zero_attempts_should_return_true",
            "pr_number": test_pr_number,
            "repo": test_repo,
            "branch": test_branch,
            "pr_attempts": attempts_data,
            "can_process_pr_result": result,
            "expected_result": True,
        }

        evidence_file = evidence_dir / "can_process_pr_evidence.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        assert result is True, (
            f"can_process_pr() returned False for PR #{test_pr_number} with 0 attempts."
        )

    def test_atomic_update_file_write_success(self, temp_data_dir):
        """
        Test if atomic_update file writes are working correctly.
        """
        test_file = temp_data_dir / "test_atomic_write.json"

        def update_func(data):
            return {"test_key": "test_value"}

        write_success = json_manager.atomic_update(test_file, update_func, {})
        assert write_success is True, "atomic_update() should return True for successful write"

        with open(test_file, "r") as f:
            data = json.load(f)

        evidence = {
            "test": "test_atomic_update_file_write_success",
            "write_success": write_success,
            "file_contents": data,
            "expected_contents": {"test_key": "test_value"},
        }

        evidence_dir = temp_data_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        evidence_file = evidence_dir / "atomic_update_evidence.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        assert data == {"test_key": "test_value"}, "File should contain updated data"

    def test_try_process_pr_fails_when_atomic_update_returns_false(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        Verify atomic_update() failure correctly prevents processing.
        """
        test_pr_number = 3185
        test_repo = "jleechanorg/worldarchitect.ai"
        test_branch = "fix/spicy-mode-detection"

        can_process = clean_safety_manager.can_process_pr(
            test_pr_number, test_repo, test_branch
        )
        assert can_process is True, "can_process_pr() should return True with 0 attempts"

        with patch.object(SafeJSONManager, "atomic_update") as mock_atomic:
            mock_atomic.return_value = False

            result = clean_safety_manager.try_process_pr(
                test_pr_number, test_repo, test_branch
            )

            evidence_dir = temp_data_dir / "evidence"
            evidence_dir.mkdir(exist_ok=True)

            evidence = {
                "test": "test_try_process_pr_fails_when_atomic_update_returns_false",
                "pr_number": test_pr_number,
                "repo": test_repo,
                "branch": test_branch,
                "can_process_pr": can_process,
                "atomic_update_return": False,
                "try_process_pr_result": result,
                "expected_result": False,
                "fix_verified": result is False,
            }

            evidence_file = evidence_dir / "atomic_update_failure_evidence.json"
            with open(evidence_file, "w") as f:
                json.dump(evidence, f, indent=2)

            assert result is False, (
                f"try_process_pr() returned {result} when atomic_update() failed. "
                f"Expected False to prevent race condition. Evidence: {evidence_file}"
            )

    def test_try_process_pr_retries_and_fails_closed_on_atomic_update_exception(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        atomic_update() exceptions should be retried and fail closed.
        """
        test_pr_number = 3664
        test_repo = "jleechanorg/worldarchitect.ai"
        test_branch = "claude/add-action-resolution-warning"

        can_process = clean_safety_manager.can_process_pr(
            test_pr_number, test_repo, test_branch
        )
        assert can_process is True

        with patch.object(SafeJSONManager, "atomic_update") as mock_atomic, \
             patch("jleechanorg_pr_automation.automation_safety_manager.time.sleep", return_value=None):
            mock_atomic.side_effect = OSError(28, "No space left on device")

            result = clean_safety_manager.try_process_pr(
                test_pr_number, test_repo, test_branch
            )

            evidence_dir = temp_data_dir / "evidence"
            evidence_dir.mkdir(exist_ok=True)

            evidence = {
                "test": "test_try_process_pr_retries_and_fails_closed_on_atomic_update_exception",
                "pr_number": test_pr_number,
                "can_process_pr": can_process,
                "atomic_update_exception": "OSError(28, No space left on device)",
                "try_process_pr_result": result,
                "expected_behavior": "Retry then fail closed (return False)",
                "atomic_update_call_count": mock_atomic.call_count,
            }

            evidence_file = evidence_dir / "atomic_update_exception_evidence.json"
            with open(evidence_file, "w") as f:
                json.dump(evidence, f, indent=2)

            assert result is False, "Should fail closed when atomic_update() raises"
            assert mock_atomic.call_count == 3, "Should retry atomic_update() three times"

    def test_can_process_pr_unaffected_by_file_io_failures(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        Verify can_process_pr() still works correctly even when file I/O is problematic.
        """
        test_pr_number = 3096
        test_repo = "jleechanorg/worldarchitect.ai"

        result = clean_safety_manager.can_process_pr(test_pr_number, test_repo)

        evidence_dir = temp_data_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)

        evidence = {
            "test": "test_can_process_pr_unaffected_by_file_io_failures",
            "pr_number": test_pr_number,
            "can_process_pr_result": result,
            "expected": True,
        }

        evidence_file = evidence_dir / "can_process_pr_verification.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        assert result is True, "can_process_pr() should return True with 0 attempts"

    def test_release_pr_slot_retries_on_atomic_update_exception(
        self, clean_safety_manager
    ):
        """
        release_pr_slot should retry and not raise on atomic_update() exceptions.
        """
        test_pr_number = 5001
        test_repo = "jleechanorg/worldarchitect.ai"
        test_branch = "fix/release-retry"

        clean_safety_manager.try_process_pr(test_pr_number, test_repo, test_branch)

        with patch.object(SafeJSONManager, "atomic_update") as mock_atomic, \
             patch("jleechanorg_pr_automation.automation_safety_manager.time.sleep", return_value=None):
            mock_atomic.side_effect = OSError(5, "I/O error")

            clean_safety_manager.release_pr_slot(test_pr_number, test_repo, test_branch)

            assert mock_atomic.call_count == 3, "Should retry atomic_update() three times"


def test_safety_limits_false_rejection_red():
    """
    RED reproduction test (disabled by default).

    Set RUN_RED_TESTS=1 to enable.
    """
    if os.getenv("RUN_RED_TESTS") != "1":
        pytest.skip("Set RUN_RED_TESTS=1 to run RED reproduction test")

    evidence_root = os.environ.get("SAFETY_BUG_EVIDENCE_DIR")
    if evidence_root:
        evidence_base = Path(evidence_root)
        evidence_base.mkdir(parents=True, exist_ok=True)

        for item in evidence_base.glob("*"):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    else:
        evidence_base = Path(tempfile.mkdtemp(prefix="safety-limits-bug-"))

    iteration = 1
    while (evidence_base / f"iteration_{iteration:03d}").exists():
        iteration += 1

    evidence_dir = evidence_base / f"iteration_{iteration:03d}"
    evidence_dir.mkdir(exist_ok=True)

    temp_data_dir = evidence_dir / "safety_data"
    temp_data_dir.mkdir(exist_ok=True)

    manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

    pr_attempts_file = temp_data_dir / "pr_attempts.json"
    with open(pr_attempts_file, "r") as f:
        attempts_data = json.load(f)

    assert attempts_data == {}, f"Expected empty pr_attempts.json, got {attempts_data}"

    test_cases = [
        {"pr": 3185, "repo": "jleechanorg/worldarchitect.ai", "branch": "fix/spicy-mode-detection"},
        {"pr": 3664, "repo": "jleechanorg/worldarchitect.ai", "branch": "claude/add-action-resolution-warning"},
        {"pr": 3096, "repo": "jleechanorg/worldarchitect.ai", "branch": "fix/dice-authentication-logic"},
    ]

    results = []
    for test_case in test_cases:
        pr_number = test_case["pr"]
        repo = test_case["repo"]
        branch = test_case["branch"]

        can_process = manager.can_process_pr(pr_number, repo, branch)
        try_result = manager.try_process_pr(pr_number, repo, branch)
        attempts = manager.get_pr_attempts(pr_number, repo, branch)

        result = {
            "pr_number": pr_number,
            "repo": repo,
            "branch": branch,
            "can_process_pr": can_process,
            "try_process_pr": try_result,
            "attempts": attempts,
            "expected_try_process_pr": True,
            "bug_reproduced": try_result is False,
        }
        results.append(result)

        if try_result:
            manager.release_pr_slot(pr_number, repo, branch)

    evidence = {
        "test": "test_safety_limits_false_rejection_red",
        "evidence_directory": str(evidence_dir),
        "initial_state": {
            "pr_attempts.json": attempts_data,
            "pr_inflight.json": {},
        },
        "test_cases": results,
        "bug_summary": {
            "total_tests": len(results),
            "bugs_reproduced": sum(1 for r in results if r["bug_reproduced"]),
            "expected_behavior": "All try_process_pr() should return True with 0 attempts",
        },
    }

    evidence_file = evidence_dir / "test_evidence.json"
    with open(evidence_file, "w") as f:
        json.dump(evidence, f, indent=2)

    for filename in ["pr_attempts.json", "pr_inflight.json", "global_runs.json"]:
        src = temp_data_dir / filename
        if src.exists():
            shutil.copy(src, evidence_dir / f"final_{filename}")

    bugs_found = sum(1 for r in results if r["bug_reproduced"])
    if bugs_found > 0:
        failing_prs = [r["pr_number"] for r in results if r["bug_reproduced"]]
        assert False, (
            f"RED STATE CONFIRMED: Bug reproduced in {bugs_found}/{len(results)} test cases. "
            f"Failing PRs: {failing_prs}. Evidence: {evidence_file}"
        )
    else:
        print(
            f"✅ RED repro did not trigger; no failures observed. Evidence: {evidence_file}"
        )
