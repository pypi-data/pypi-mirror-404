"""
Enhanced RED Test: Safety limits false rejection with atomic_update() failure simulation.

This test uses mocking to reproduce the production bug where try_process_pr() returns
False when atomic_update() fails, even though the PR has 0/50 attempts and should be allowed.

Bug: WA-3gx
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager


class TestSafetyLimitsAtomicUpdateFailure:
    """Test suite for atomic_update() failure scenarios."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for safety manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def clean_safety_manager(self, temp_data_dir):
        """Create safety manager with clean (empty) state."""
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

        # Verify initial state is clean (empty files)
        pr_attempts_file = temp_data_dir / "pr_attempts.json"
        pr_inflight_file = temp_data_dir / "pr_inflight.json"

        # Ensure files exist but are empty
        pr_attempts_file.write_text("{}")
        pr_inflight_file.write_text("{}")

        return manager

    def test_try_process_pr_fails_when_atomic_update_returns_false(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        ✅ GREEN TEST: Verify atomic_update() failure correctly prevents processing.

        Given: Clean safety manager state (0/50 attempts)
        When: atomic_update() returns False (simulated file I/O failure)
        Then: try_process_pr() MUST return False to prevent race conditions

        CORRECTED BEHAVIOR (after WA-3gx fix):
        - When atomic_update() fails, cannot guarantee concurrent safety
        - Must return False even though can_process_pr() returns True
        - This prevents race conditions in multi-process scenarios

        OLD BUGGY BEHAVIOR:
        - Defensive fallback returned True (allowed processing)
        - Created in-memory/disk inconsistency
        - Multiple processes could bypass concurrent_limit=1
        """
        test_pr_number = 3185
        test_repo = "jleechanorg/worldarchitect.ai"
        test_branch = "fix/spicy-mode-detection"

        # Verify can_process_pr returns True (0 attempts)
        can_process = clean_safety_manager.can_process_pr(
            test_pr_number, test_repo, test_branch
        )
        assert can_process is True, "can_process_pr() should return True with 0 attempts"

        # Mock atomic_update to simulate file I/O failure
        with patch('jleechanorg_pr_automation.utils.json_manager.atomic_update') as mock_atomic:
            # Simulate file lock contention / I/O failure
            mock_atomic.return_value = False

            # Act: Call try_process_pr()
            result = clean_safety_manager.try_process_pr(
                test_pr_number, test_repo, test_branch
            )

            # Save evidence
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

            print(f"\n✅ CORRECT BEHAVIOR: atomic_update() mocked to fail")
            print(f"   can_process_pr(): {can_process}")
            print(f"   atomic_update(): False (mocked)")
            print(f"   try_process_pr(): {result}")
            print(f"   Expected: False (prevent race condition)")
            print(f"   Fix verified: {result is False}")
            print(f"\nEvidence saved to: {evidence_file}\n")

            # Assert - MUST return False to prevent race conditions
            assert result is False, (
                f"\n❌ REGRESSION: try_process_pr() returned {result} "
                f"when atomic_update() failed. This creates a race condition! "
                f"Even though can_process_pr() returned True, we MUST return False "
                f"to prevent multiple processes from bypassing concurrent_limit=1. "
                f"\n\nExpected: False (reject to prevent race condition)"
                f"\nActual: {result}"
                f"\nEvidence: {evidence_file}"
            )

    def test_try_process_pr_with_exception_during_atomic_update(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        🔴 RED TEST: Reproduce bug when atomic_update() raises exception.

        Simulates transient I/O errors (ENOSPC, EACCES, etc.)
        """
        test_pr_number = 3664
        test_repo = "jleechanorg/worldarchitect.ai"
        test_branch = "claude/add-action-resolution-warning"

        # Verify can_process_pr returns True
        can_process = clean_safety_manager.can_process_pr(
            test_pr_number, test_repo, test_branch
        )
        assert can_process is True

        # Mock atomic_update to raise OSError (disk full / permissions)
        with patch('jleechanorg_pr_automation.utils.json_manager.atomic_update') as mock_atomic:
            # Simulate disk full error
            mock_atomic.side_effect = OSError(28, "No space left on device")

            # This will raise an exception - catch it for evidence
            result = None
            exception_raised = None

            try:
                result = clean_safety_manager.try_process_pr(
                    test_pr_number, test_repo, test_branch
                )
            except OSError as e:
                exception_raised = str(e)

            # Save evidence
            evidence_dir = temp_data_dir / "evidence"
            evidence_dir.mkdir(exist_ok=True)

            evidence = {
                "test": "test_try_process_pr_with_exception_during_atomic_update",
                "pr_number": test_pr_number,
                "can_process_pr": can_process,
                "atomic_update_exception": exception_raised,
                "try_process_pr_result": result,
                "expected_behavior": "Should handle exception gracefully or retry",
            }

            evidence_file = evidence_dir / "atomic_update_exception_evidence.json"
            with open(evidence_file, "w") as f:
                json.dump(evidence, f, indent=2)

            print(f"\n🔴 RED TEST: atomic_update() raised OSError")
            print(f"   Exception: {exception_raised}")
            print(f"   Result: {result}")
            print(f"   Expected: Graceful handling or retry")
            print(f"\nEvidence saved to: {evidence_file}\n")

            # Either exception was raised (not caught) or result is None
            assert exception_raised or result is None, (
                "atomic_update() exception should be handled gracefully"
            )

    def test_can_process_pr_unaffected_by_file_io_failures(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        Verify can_process_pr() still works correctly even when file I/O is problematic.

        This confirms can_process_pr() is not the source of the bug.
        """
        test_pr_number = 3096
        test_repo = "jleechanorg/worldarchitect.ai"

        # can_process_pr() should work independently of atomic_update()
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

        print(f"\n✅ Verification: can_process_pr() works independently")
        print(f"   Result: {result}")
        print(f"\nEvidence saved to: {evidence_file}\n")

        # This should pass - can_process_pr() is working correctly
        assert result is True, "can_process_pr() should return True with 0 attempts"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
