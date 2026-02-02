"""
TraceMon - Per-trace monitoring and logging
==========================================

TraceMon is designed for complete trace isolation. Each request/operation gets
its own TraceMon instance, eliminating race conditions and providing clean,
per-trace context management.

Key Design Principles:
1. One TraceMon per trace (complete isolation)
2. No shared state between traces
3. Automatic trace_id inference (no parameter needed)
4. Thread-safe by design
5. Collector ID and trace_id are the same (one collector per trace)
"""
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from contextlib import contextmanager
from collections import defaultdict
from ipulse_shared_base_ftredge import (LogLevel, AbstractResource,
                                      ProgressStatus, Action,
                                      Alert, StructLog)
from ipulse_shared_base_ftredge.status import StatusCounts, map_progress_status_to_log_level, eval_statuses


class TraceMon:
    """
    TraceMon handles monitoring and logging for a single trace/request.

    Each trace gets its own TraceMon instance, providing complete isolation
    and eliminating race conditions between concurrent requests.
    """

    def __init__(self, base_context: str, logger,
                 max_log_field_len: Optional[int] = 8000,  # by default PipelineLog has 8000 per field length Limit
                 max_log_dict_byte_size: Optional[float] = 256 * 1024 * 0.80,  # by default PipelineLog dict has 256 * 1024 * 0.80 -80% of 256Kb Limit
                 exclude_none_from_logs: bool = True):
        """
        Initialize TraceMon for a single trace.

        Args:
            base_context: Base context containing all execution details
            logger: Logger instance to use
            max_log_field_len: Maximum length for log field values
            max_log_dict_byte_size: Maximum byte size for log dictionary
            exclude_none_from_logs: Whether to exclude None values from logs
        """
        # Create ID with timestamp prefix and UUID suffix (same pattern as pipelinemon)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        uuid_suffix = str(uuid.uuid4())[:8]  # Take first 8 chars of UUID
        self._id = f"{timestamp}_{uuid_suffix}"

        # Core configuration
        self._logger = logger
        self._base_context = base_context

        # Logging configuration
        self._max_log_field_len = max_log_field_len
        self._max_log_dict_byte_size = max_log_dict_byte_size
        self._exclude_none_from_logs = exclude_none_from_logs

        # Trace timing
        self._start_time = time.time()
        self._end_time: Optional[float] = None

        # Context stack (isolated per trace)
        self._context_stack = []

        # Trace metrics
        self._metrics = {
            "trace_id": self._id,  # In TraceMon, collector_id and trace_id are the same
            "start_time": self._start_time,
            "status": str(ProgressStatus.IN_PROGRESS),
            "by_event_count": defaultdict(int),
            "by_level_code_count": defaultdict(int),
            "status_counts": StatusCounts()
        }

        # Add initial status
        self._metrics["status_counts"].add_status(ProgressStatus.STARTED)

        # Log trace start
        self._log_trace_start()

    @property
    def id(self) -> str:
        """Get the unique ID for this TraceMon (both collector_id and trace_id)."""
        return self._id

    @property
    def trace_id(self) -> str:
        """Get the trace ID for this trace (same as collector_id)."""
        return self._id

    @property
    def collector_id(self) -> str:
        """Get the collector ID for this TraceMon (same as trace_id)."""
        return self._id

    @property
    def base_context(self) -> str:
        """Get the base context."""
        return self._base_context

    @property
    def current_context(self) -> str:
        """Get the current context stack as a string."""
        if not self._context_stack:
            return self._id
        return f"{self._id} >> " + " >> ".join(self._context_stack)

    @property
    def elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds since trace start."""
        return int((time.time() - self._start_time) * 1000)

    @property
    def duration_ms(self) -> Optional[int]:
        """Get total duration in milliseconds (only available after end)."""
        if self._end_time is None:
            return None
        return int((self._end_time - self._start_time) * 1000)

    @property
    def metrics(self) -> Dict[str, Any]:
        """Get current trace metrics."""
        metrics = self._metrics.copy()
        metrics["by_event_count"] = dict(metrics["by_event_count"])
        metrics["by_level_code_count"] = dict(metrics["by_level_code_count"])
        metrics["elapsed_ms"] = self.elapsed_ms
        if self.duration_ms is not None:
            metrics["duration_ms"] = self.duration_ms
        return metrics

    @property
    def is_active(self) -> bool:
        """Check if trace is still active (not ended)."""
        return self._end_time is None

    def _log_trace_start(self):
        """Log the trace start event."""
        start_log = StructLog(
            level=LogLevel.INFO,
            description=f"Starting trace {self._id}",
            resource=AbstractResource.TRACEMON,
            action=Action.EXECUTE,
            progress_status=ProgressStatus.STARTED,
        )
        self.log(start_log)

    @contextmanager
    def context(self, context_name: str):
        """
        Context manager for tracking execution context within this trace.

        Args:
            context_name: The name of the execution context
        """
        self.push_context(context_name)
        try:
            yield
        finally:
            self.pop_context()

    def push_context(self, context: str):
        """Add a context level to the stack."""
        self._context_stack.append(context)

    def pop_context(self):
        """Remove the most recent context from the stack."""
        if self._context_stack:
            return self._context_stack.pop()

    def log(self, log: StructLog) -> None:
        """
        Log a StructLog message with this trace's context.

        Args:
            log: StructLog instance to log
        """
        if not self.is_active:
            # Still allow logging but add a warning note
            existing_note = log.note or ""
            warning_note = "TRACE_ENDED"
            log.note = f"{existing_note}; {warning_note}" if existing_note else warning_note

        # Set trace-specific context
        log.trace_id = self._id
        log.collector_id = self._id
        log.base_context = self._base_context
        log.context = self.current_context

        # Add elapsed time
        existing_note = log.note or ""
        elapsed_note = f"elapsed_ms: {self.elapsed_ms}"
        log.note = f"{existing_note}; {elapsed_note}" if existing_note else elapsed_note

        # Update trace metrics
        self._update_counts(log)

        # Write to logger
        self._write_log_to_logger(log)

    def _update_counts(self, log: StructLog):
        """Update trace metrics based on the log event."""
        event_tuple = log.getEvent()
        level = log.level

        self._metrics["by_event_count"][event_tuple] += 1
        self._metrics["by_level_code_count"][level.value] += 1

    def _get_error_count(self) -> int:
        """Get total error count (ERROR + CRITICAL)."""
        return (self._metrics["by_level_code_count"].get(LogLevel.ERROR.value, 0) +
                self._metrics["by_level_code_count"].get(LogLevel.CRITICAL.value, 0))

    def _get_warning_count(self) -> int:
        """Get warning count."""
        return self._metrics["by_level_code_count"].get(LogLevel.WARNING.value, 0)

    def _get_notice_count(self) -> int:
        """Get notice count."""
        return self._metrics["by_level_code_count"].get(LogLevel.NOTICE.value, 0)

    def end(self, force_status: Optional[ProgressStatus] = None, issues_allowed: bool = True) -> Dict[str, Any]:
        """
        End this trace and return final metrics.

        Args:
            force_status: Optional status to force, overriding automatic calculation
            issues_allowed: Whether issues (errors) are allowed for this trace

        Returns:
            Dict containing final trace metrics
        """
        if not self.is_active:
            # Already ended, return existing metrics
            return self.metrics

        self._end_time = time.time()

        # Calculate final status
        error_count = self._get_error_count()
        warning_count = self._get_warning_count()
        notice_count = self._get_notice_count()

        if force_status is not None:
            final_status = force_status
            level = map_progress_status_to_log_level(final_status)
        else:
            # Simple status calculation based on error/warning/notice counts
            if error_count > 0:
                if issues_allowed:
                    final_status = ProgressStatus.FINISHED_WITH_ISSUES
                else:
                    final_status = ProgressStatus.FAILED
            elif warning_count > 0:
                final_status = ProgressStatus.DONE_WITH_WARNINGS
            elif notice_count > 0:
                final_status = ProgressStatus.DONE_WITH_NOTICES
            else:
                final_status = ProgressStatus.DONE

            level = map_progress_status_to_log_level(final_status)

        # Update trace status
        self._metrics["status"] = str(final_status)
        self._metrics["status_counts"].add_status(final_status)

        # Log completion
        status_source = "FORCED" if force_status is not None else "AUTO"
        summary_msg = (
            f"Trace {self._id} completed with status {str(final_status)} ({status_source}). "
            f"Duration: {self.duration_ms}ms. "
            f"Errors: {error_count}, Warnings: {warning_count}, Notices: {notice_count}"
        )

        completion_log = StructLog(
            level=level,
            description=summary_msg,
            resource=AbstractResource.TRACEMON,
            action=Action.EXECUTE,
            progress_status=final_status
        )
        self.log(completion_log)

        return self.metrics

    def get_readable_level_counts(self) -> Dict[str, int]:
        """Get readable level counts for this trace."""
        readable_counts = {}

        for level_code, count in self._metrics["by_level_code_count"].items():
            if count > 0:
                for level in LogLevel:
                    if level.value == level_code:
                        readable_counts[str(level)] = count
                        break

        return readable_counts

    def _write_log_to_logger(self, log: StructLog):
        """Write structured log to the logger."""
        log_dict = log.to_dict(
            max_field_len=self._max_log_field_len,
            byte_size_limit=self._max_log_dict_byte_size,
            exclude_none=self._exclude_none_from_logs
        )

        # Write to logger based on level
        if log.level.value >= LogLevel.ERROR.value:
            self._logger.error(log_dict)
        elif log.level.value >= LogLevel.WARNING.value:
            self._logger.warning(log_dict)
        elif log.level.value >= LogLevel.INFO.value:
            self._logger.info(log_dict)
        else:
            self._logger.debug(log_dict)
