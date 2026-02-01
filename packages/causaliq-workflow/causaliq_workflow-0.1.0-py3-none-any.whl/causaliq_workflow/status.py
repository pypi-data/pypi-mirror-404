"""Task execution status enumeration for workflow logging system.

This module defines the TaskStatus enum which provides standardized status
reporting for workflow task execution across different modes (run, dry-run,
compare) and execution outcomes.
"""

from enum import Enum


class TaskStatus(Enum):
    """Enumeration of all possible task execution statuses.

    Provides standardized status reporting for workflow task execution,
    supporting different execution modes and comprehensive error
    categorization.

    Status Categories:
        - Execution: EXECUTES, WOULD_EXECUTE, SKIPS, WOULD_SKIP
        - Comparison: IDENTICAL, DIFFERENT
        - Errors: INVALID_USES, INVALID_PARAMETER, FAILED, TIMED_OUT
    """

    # Core execution statuses
    EXECUTES = "EXECUTES"
    """Task executed successfully, output files created/updated."""

    WOULD_EXECUTE = "WOULD_EXECUTE"
    """Task would execute successfully if run (dry-run mode)."""

    SKIPS = "SKIPS"
    """Task skipped because output files exist and are current."""

    WOULD_SKIP = "WOULD_SKIP"
    """Task would be skipped because output files exist (dry-run mode)."""

    # Compare mode statuses
    IDENTICAL = "IDENTICAL"
    """Task re-executed, outputs identical to previous run."""

    DIFFERENT = "DIFFERENT"
    """Task re-executed, outputs differ from previous run."""

    # Error statuses
    INVALID_USES = "INVALID_USES"
    """Action package specified in uses: not found."""

    INVALID_PARAMETER = "INVALID_PARAMETER"
    """Parameters in with: block are invalid for action."""

    FAILED = "FAILED"
    """Task execution threw unexpected exception."""

    TIMED_OUT = "TIMED_OUT"
    """Task exceeded configured timeout."""

    @property
    def is_success(self) -> bool:
        """Return True if status indicates successful execution."""
        return self in {
            self.EXECUTES,
            self.WOULD_EXECUTE,
            self.SKIPS,
            self.WOULD_SKIP,
            self.IDENTICAL,
            self.DIFFERENT,
        }

    @property
    def is_error(self) -> bool:
        """Return True if status indicates an error condition."""
        return self in {
            self.INVALID_USES,
            self.INVALID_PARAMETER,
            self.FAILED,
            self.TIMED_OUT,
        }

    @property
    def is_execution(self) -> bool:
        """Return True if status indicates actual execution occurred."""
        return self in {self.EXECUTES, self.IDENTICAL, self.DIFFERENT}

    @property
    def is_dry_run(self) -> bool:
        """Return True if status is for dry-run mode."""
        return self in {self.WOULD_EXECUTE, self.WOULD_SKIP}
