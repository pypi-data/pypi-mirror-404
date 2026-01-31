#!/usr/bin/env python3
"""
🔴 RED TEST: Regression test for WA-3gx defensive fallback race condition

PROBLEM:
When atomic_update() fails at line 537 in try_process_pr():
1. reserve_slot() callback has ALREADY modified in-memory cache (line 532)
2. BUT disk file pr_inflight.json was NOT updated (write failed)
3. Code returns True, allowing process A to proceed
4. Process B calls try_process_pr(), reads disk (inflight=0), also succeeds
5. RESULT: TWO processes concurrently process same PR (violates concurrent_limit=1)

ROOT CAUSE:
- Line 540-553: Defensive fallback returns True after atomic_update() fails
- In-memory cache has inflight+1, but disk has old value
- Other processes read stale data from disk
- Multi-process race condition bypasses concurrent_limit

EXPECTED BEHAVIOR:
- If atomic_update() fails, must return False
- Cannot allow processing without successful disk synchronization
- Concurrent processing limit MUST be enforced across all processes

This test reproduces the exact race condition using multiprocessing.
"""

import json
import multiprocessing
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.utils import SafeJSONManager


def _try_process_with_atomic_failure(pr_number: int, data_dir: str, process_id: int):
    """
    Simulate a process calling try_process_pr() where atomic_update() fails.

    This simulates the bug condition:
    - can_process_pr() returns True (0 attempts)
    - atomic_update() fails (file I/O error)
    - Current bug: returns True (WRONG - allows concurrent processing)
    - Expected: should return False (prevent race condition)
    """
    manager = AutomationSafetyManager(data_dir=data_dir)

    # Mock atomic_update to fail on first call for this process
    with patch('jleechanorg_pr_automation.utils.json_manager.atomic_update') as mock_atomic:
        # Simulate file I/O failure (disk full, lock contention, etc.)
        mock_atomic.return_value = False

        # Try to process PR
        result = manager.try_process_pr(pr_number, repo="test-repo", branch="test-branch")

        return (result, process_id, "atomic_update_failed")


def _try_process_normal(pr_number: int, data_dir: str, process_id: int):
    """
    Simulate a normal process calling try_process_pr() without mocking.

    This process reads from disk (should see inflight=0 if other process failed to write).
    Without the fix, this process will ALSO succeed, violating concurrent_limit=1.
    """
    manager = AutomationSafetyManager(data_dir=data_dir)

    # Small delay to ensure first process has attempted (and failed) to write
    time.sleep(0.05)

    result = manager.try_process_pr(pr_number, repo="test-repo", branch="test-branch")

    # Check what disk actually says
    inflight_file = Path(data_dir) / "pr_inflight.json"
    with open(inflight_file) as f:
        disk_data = json.load(f)

    pr_key = f"r=test-repo||p={pr_number}||b=test-branch"
    disk_inflight = disk_data.get(pr_key, {}).get("count", 0) if isinstance(disk_data.get(pr_key), dict) else disk_data.get(pr_key, 0)

    return (result, process_id, "normal_process", disk_inflight)


def test_regression_wa3gx_defensive_fallback_race_condition(tmp_path):
    """
    🔴 RED TEST: Reproduce the race condition caused by defensive fallback.

    Given:
    - Process A calls try_process_pr()
    - atomic_update() fails (file I/O error)
    - Defensive fallback returns True (BUG)
    - In-memory has inflight=1, disk has inflight=0

    When:
    - Process B calls try_process_pr()
    - Reads disk, sees inflight=0
    - Also returns True

    Then:
    - BOTH processes are processing same PR concurrently
    - Violates concurrent_limit=1
    - Race condition occurs

    This test MUST FAIL with current code (RED state).
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    # Initialize empty files
    SafeJSONManager().write_json(str(safety_data_dir / "pr_attempts.json"), {})
    SafeJSONManager().write_json(str(safety_data_dir / "pr_inflight.json"), {})
    SafeJSONManager().write_json(str(safety_data_dir / "global_runs.json"), {})

    pr_number = 3185

    # Run two processes concurrently
    pool = multiprocessing.Pool(processes=2)

    # Process A: atomic_update() fails (mocked)
    result_a = pool.apply_async(_try_process_with_atomic_failure, (pr_number, str(safety_data_dir), 1))

    # Small delay to let Process A start first
    time.sleep(0.01)

    # Process B: normal call (reads from disk)
    result_b = pool.apply_async(_try_process_normal, (pr_number, str(safety_data_dir), 2))

    pool.close()
    pool.join()

    # Get results
    outcome_a = result_a.get()  # (result, process_id, status)
    outcome_b = result_b.get()  # (result, process_id, status, disk_inflight)

    success_a, pid_a, status_a = outcome_a
    success_b, pid_b, status_b, disk_inflight = outcome_b

    print(f"\n🔍 Race Condition Test Results:")
    print(f"  Process A (atomic_update failed): success={success_a}, status={status_a}")
    print(f"  Process B (normal): success={success_b}, status={status_b}, disk_inflight={disk_inflight}")

    # 🔴 RED ASSERTION: This SHOULD FAIL with current buggy code
    #
    # Current buggy behavior:
    # - Process A: atomic_update() fails → defensive fallback returns True → success_a=True
    # - Process B: reads disk (inflight=0) → returns True → success_b=True
    # - BOTH succeed (RACE CONDITION!)
    #
    # Expected correct behavior:
    # - Process A: atomic_update() fails → returns False → success_a=False
    # - Process B: reads disk (inflight=0) → returns True → success_b=True
    # - ONLY ONE succeeds (concurrent_limit=1 enforced)

    if success_a and success_b:
        pytest.fail(
            f"\n🔴 RACE CONDITION DETECTED (WA-3gx bug reproduced):\n"
            f"  Process A succeeded despite atomic_update() failure (defensive fallback bug)\n"
            f"  Process B also succeeded (read stale disk data: inflight={disk_inflight})\n"
            f"  BOTH processes are now processing PR #{pr_number} concurrently!\n"
            f"  This violates concurrent_limit=1 invariant.\n\n"
            f"Root cause: automation_safety_manager.py:540-553 defensive fallback\n"
            f"  - Returns True when atomic_update() fails\n"
            f"  - In-memory cache modified but disk not updated\n"
            f"  - Other processes read stale data from disk\n\n"
            f"Expected: Process A should return False (cannot guarantee concurrent safety)\n"
            f"Actual: Process A returned True (bypassed disk synchronization)"
        )

    # Correct behavior assertion (will pass after fix)
    assert not (success_a and success_b), (
        "At most ONE process should succeed. "
        f"Got: Process A={success_a}, Process B={success_b}"
    )

    # After fix, exactly one should succeed
    total_successes = sum([success_a, success_b])
    assert total_successes == 1, (
        f"Expected exactly 1 success (concurrent_limit=1), got {total_successes}"
    )


def test_regression_wa3gx_in_memory_disk_inconsistency():
    """
    ✅ GREEN TEST: Verify that atomic_update() failure does NOT create inconsistency.

    When atomic_update() fails (after fix):
    - try_process_pr() returns False immediately
    - reserve_slot() callback is executed but disk write fails
    - In-memory cache IS modified by callback (unavoidable)
    - BUT we return False, so no processing happens
    - No race condition because we rejected the request

    OLD BUGGY BEHAVIOR:
    - Returned True despite write failure
    - Created in-memory/disk inconsistency
    - Other processes could bypass concurrent_limit

    FIXED BEHAVIOR:
    - Returns False despite write failure
    - Prevents race condition by rejecting request
    - In-memory inconsistency exists but is harmless (request was rejected)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = AutomationSafetyManager(data_dir=tmpdir)

        pr_number = 3664
        repo = "test-repo"
        branch = "test-branch"

        # Mock atomic_update to fail
        with patch('jleechanorg_pr_automation.utils.json_manager.atomic_update') as mock_atomic:
            mock_atomic.return_value = False

            # Call try_process_pr() - should return False (fix)
            result = manager.try_process_pr(pr_number, repo, branch)

            # ✅ FIX VERIFIED: Returns False to prevent race condition
            assert result is False, (
                f"❌ REGRESSION: try_process_pr() returned {result} "
                f"when atomic_update() failed. Expected False to prevent race condition."
            )

            # Check in-memory cache - may be modified by callback (harmless since we returned False)
            pr_key = manager._make_pr_key(pr_number, repo, branch)
            in_memory_count = manager._pr_inflight_cache.get(pr_key, 0)

            # Check disk
            inflight_file = Path(tmpdir) / "pr_inflight.json"
            with open(inflight_file) as f:
                disk_data = json.load(f)

            disk_count = disk_data.get(pr_key, {}).get("count", 0) if isinstance(disk_data.get(pr_key), dict) else disk_data.get(pr_key, 0)

            print(f"\n✅ CORRECT BEHAVIOR: atomic_update() failed")
            print(f"  try_process_pr(): {result} (rejected)")
            print(f"  In-memory cache: inflight={in_memory_count}")
            print(f"  Disk file: inflight={disk_count}")
            print(f"  Race condition prevented: {result is False}")

            # In-memory inconsistency may exist, but it's harmless because:
            # 1. We returned False (no processing allowed)
            # 2. Next call will reload from disk anyway
            # The key is that we REJECTED the request to prevent race conditions


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
