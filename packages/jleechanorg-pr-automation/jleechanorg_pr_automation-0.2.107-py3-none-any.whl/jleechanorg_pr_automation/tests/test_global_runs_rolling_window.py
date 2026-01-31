#!/usr/bin/env python3
"""
🔴 RED TEST: Rolling window for global runs

PROBLEM:
Global runs currently use daily reset (midnight), causing sudden availability
changes. A system with 49/50 runs at 11:59 PM suddenly resets to 0/50 at midnight,
allowing 50 more runs even though the last 24 hours had 99 total runs.

SOLUTION:
Implement rolling 24-hour window for global runs (like PR attempts):
- Store list of run timestamps
- Count only runs in last 24 hours
- Runs gradually age out of the window
- No sudden resets at midnight
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.utils import SafeJSONManager


class TestGlobalRunsRollingWindow:
    """Test suite for rolling window global run limiting."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for safety manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize empty files
            SafeJSONManager().write_json(str(Path(tmpdir) / "pr_attempts.json"), {})
            SafeJSONManager().write_json(str(Path(tmpdir) / "pr_inflight.json"), {})
            SafeJSONManager().write_json(str(Path(tmpdir) / "global_runs.json"), {})
            yield Path(tmpdir)

    def test_global_runs_use_rolling_window(self, temp_data_dir):
        """
        🔴 RED TEST: Verify global runs use rolling 24-hour window.

        Given: Global limit of 100, runs recorded over 30 hours
        When: Checking can_start_global_run() after 25 hours
        Then: Should only count runs in last 24 hours (not all time)
        """
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir), limits={"global_limit": 100})

        # Simulate 50 runs from 30 hours ago
        base_time = datetime.now(timezone.utc) - timedelta(hours=30)
        for i in range(50):
            # Manually record with old timestamp
            run_time = base_time + timedelta(minutes=i)
            manager._record_global_run_at_time(run_time)

        # Simulate 40 runs from 2 hours ago
        recent_time = datetime.now(timezone.utc) - timedelta(hours=2)
        for i in range(40):
            run_time = recent_time + timedelta(minutes=i)
            manager._record_global_run_at_time(run_time)

        # Get current count (should only count recent 40, not old 50)
        current_runs = manager.get_global_runs()

        # Old runs (30 hours ago) should be outside 24-hour window
        assert current_runs == 40, (
            f"Expected 40 runs in last 24 hours (50 older runs excluded), got {current_runs}"
        )

        # Should allow more runs (40 < 100)
        assert manager.can_start_global_run() is True, (
            "Should allow run when 40/100 in rolling window"
        )

        print(f"\n✅ ROLLING WINDOW TEST:")
        print(f"   Runs in last 24h: {current_runs}/100")
        print(f"   Old runs (>24h): excluded (50 runs)")
        print(f"   Can start: {manager.can_start_global_run()}")

    def test_global_runs_exclude_old_runs(self, temp_data_dir):
        """
        🔴 RED TEST: Verify old runs (>24h) are excluded from count.

        Given: 100 runs recorded 26-48 hours ago, 0 recent runs
        When: Checking current run count
        Then: Should return 0 (all runs outside window)
        """
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir), limits={"global_limit": 100})

        # Record 100 runs spread over 26-48 hours ago (ALL outside 24h window)
        for i in range(100):
            # Start at 48 hours ago, space runs 13 minutes apart
            # This ensures even the most recent run is >24h old
            hours_ago = 48 - (i * 13 / 60)  # Oldest at 48h, newest at ~26h
            run_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            manager._record_global_run_at_time(run_time)

        # All runs should be excluded (>24h old)
        current_runs = manager.get_global_runs()
        assert current_runs == 0, (
            f"Expected 0 runs in last 24 hours (100 older runs excluded), got {current_runs}"
        )

        # Should allow new runs
        assert manager.can_start_global_run() is True

        print(f"\n✅ OLD RUNS EXCLUDED TEST:")
        print(f"   Runs in last 24h: {current_runs}/100")
        print(f"   Old runs (>24h): 100 runs excluded")

    def test_global_runs_enforce_limit_in_window(self, temp_data_dir):
        """
        🔴 RED TEST: Verify limit enforced within rolling window.

        Given: 100 runs in last 24 hours (at limit)
        When: Checking can_start_global_run()
        Then: Should return False (limit reached in window)
        """
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir), limits={"global_limit": 100})

        # Record 100 runs spread over last 20 hours (within window)
        base_time = datetime.now(timezone.utc) - timedelta(hours=20)
        for i in range(100):
            run_time = base_time + timedelta(minutes=i * 12)  # Every 12 minutes
            manager._record_global_run_at_time(run_time)

        # Should hit limit
        current_runs = manager.get_global_runs()
        assert current_runs == 100, f"Expected 100 runs, got {current_runs}"

        # Should block new runs
        assert manager.can_start_global_run() is False, (
            "Should block run when at 100/100 limit"
        )

        print(f"\n✅ LIMIT ENFORCEMENT TEST:")
        print(f"   Runs in last 24h: {current_runs}/100")
        print(f"   Can start: {manager.can_start_global_run()}")

    def test_global_runs_gradual_expiration(self, temp_data_dir):
        """
        🔴 RED TEST: Verify runs gradually age out of window (no midnight reset).

        Given: System at 100/100 limit
        When: Old runs age out of 24-hour window
        Then: Capacity gradually increases (not sudden reset)
        """
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir), limits={"global_limit": 100})

        # Simulate 100 runs: 50 from 25 hours ago, 50 from 1 hour ago
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        for i in range(50):
            run_time = old_time + timedelta(minutes=i)
            manager._record_global_run_at_time(run_time)

        recent_time = datetime.now(timezone.utc) - timedelta(hours=1)
        for i in range(50):
            run_time = recent_time + timedelta(minutes=i)
            manager._record_global_run_at_time(run_time)

        # Only 50 runs should count (old 50 excluded)
        current_runs = manager.get_global_runs()
        assert current_runs == 50, (
            f"Expected 50 runs (50 old excluded), got {current_runs}"
        )

        # Should allow more runs (gradual increase, not sudden reset)
        assert manager.can_start_global_run() is True

        print(f"\n✅ GRADUAL EXPIRATION TEST:")
        print(f"   Runs in last 24h: {current_runs}/100")
        print(f"   Capacity available: {100 - current_runs}")

    def test_global_runs_configurable_window(self, temp_data_dir, monkeypatch):
        """
        ✅ GREEN TEST: Verify rolling window hours configurable via env var.

        Given: AUTOMATION_GLOBAL_WINDOW_HOURS=12 (12-hour window)
        When: Checking runs in last 12 hours
        Then: Should only count runs within 12-hour window
        """
        # Set custom window
        monkeypatch.setenv("AUTOMATION_GLOBAL_WINDOW_HOURS", "12")

        manager = AutomationSafetyManager(data_dir=str(temp_data_dir), limits={"global_limit": 100})

        # Record runs at different times
        times = [
            datetime.now(timezone.utc) - timedelta(hours=15),  # Outside 12h window
            datetime.now(timezone.utc) - timedelta(hours=10),  # Inside 12h window
            datetime.now(timezone.utc) - timedelta(hours=5),   # Inside 12h window
            datetime.now(timezone.utc) - timedelta(hours=1),   # Inside 12h window
        ]

        for run_time in times:
            manager._record_global_run_at_time(run_time)

        # Should only count 3 runs (last 3 within 12h window)
        current_runs = manager.get_global_runs()
        assert current_runs == 3, (
            f"Expected 3 runs in last 12 hours (1 older excluded), got {current_runs}"
        )

        print(f"\n✅ CONFIGURABLE WINDOW TEST:")
        print(f"   Window: 12 hours")
        print(f"   Runs in window: {current_runs}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
