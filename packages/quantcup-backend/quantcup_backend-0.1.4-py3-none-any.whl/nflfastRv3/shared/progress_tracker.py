"""
Progress Tracking for nflfastRv3

Copied from proven v1/v2 implementations with minimal modifications for v3 compatibility.
Provides intelligent progress tracking for large data operations with configurable reporting.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from commonv2 import get_logger


class ProgressTracker:
    """
    Intelligent progress tracking for large data operations with configurable reporting.
    Provides throughput calculation, ETA estimation, and batch-based progress updates.
    
    Proven implementation from v1/v2 with v3 compatibility updates.
    """
    
    def __init__(self,
                 total_expected: Optional[int] = None,
                 table_name: str = "operation",
                 chunk_size: int = 50000,
                 report_interval: int = 5,
                 tracking_unit: str = "rows",
                 logger=None):
        """
        Initialize progress tracker.
        
        Args:
            total_expected: Expected total number of items (if known)
            table_name: Name of operation being processed
            chunk_size: Size of each processing chunk
            report_interval: Report progress every N chunks
            tracking_unit: Unit being tracked ("rows", "steps", "sources", etc.)
            logger: Logger instance to use
        """
        self.total_expected = total_expected
        self.table_name = table_name
        self.chunk_size = chunk_size
        self.report_interval = report_interval
        self.tracking_unit = tracking_unit
        self.logger = logger or get_logger('nflfastRv3.progress_tracker')
        
        # Track if total was provided upfront (for reliable percentage calculation)
        self._total_was_provided_upfront = total_expected is not None
        
        # Progress tracking
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.total_processed = 0
        self.chunks_processed = 0
        self.chunk_times = []
        
        # Performance metrics
        self.throughput_history = []
        self.avg_chunk_time = 0
        
    def start(self) -> None:
        """Start progress tracking and log initial message."""
        self.start_time = time.time()
        self.last_report_time = self.start_time
        
        if self.total_expected:
            if self.tracking_unit == "rows":
                self.logger.info(f"📊 {self.table_name}: Processing ~{self.total_expected:,} {self.tracking_unit} in chunks of {self.chunk_size:,}...")
            else:
                self.logger.info(f"📊 {self.table_name}: Processing {self.total_expected} {self.tracking_unit}...")
        else:
            if self.tracking_unit == "rows":
                self.logger.info(f"📊 {self.table_name}: Processing in chunks of {self.chunk_size:,}...")
            else:
                self.logger.info(f"📊 {self.table_name}: Processing {self.tracking_unit}...")
    
    def update(self, items_processed: int, force_report: bool = False, step_name: Optional[str] = None) -> None:
        """
        Update progress with newly processed items.
        
        Args:
            items_processed: Number of items processed in this chunk
            force_report: Force a progress report regardless of interval
            step_name: Optional name of the step (for pipeline tracking)
        """
        current_time = time.time()
        chunk_duration = current_time - self.last_report_time
        
        # Update counters
        self.total_processed += items_processed
        self.chunks_processed += 1
        self.chunk_times.append(chunk_duration)
        
        # Calculate throughput for this chunk
        if chunk_duration > 0:
            chunk_throughput = items_processed / chunk_duration
            self.throughput_history.append(chunk_throughput)
            
            # Keep only recent throughput measurements for better ETA
            if len(self.throughput_history) > 10:
                self.throughput_history = self.throughput_history[-10:]
        
        # Update average chunk time
        if self.chunk_times:
            self.avg_chunk_time = sum(self.chunk_times[-5:]) / min(len(self.chunk_times), 5)
        
        # Report progress based on interval or force
        should_report = (
            force_report or 
            self.chunks_processed % self.report_interval == 0 or
            self.chunks_processed == 1  # Always report first chunk
        )
        
        if should_report:
            self._report_progress(step_name)
        
        self.last_report_time = current_time
    
    def _report_progress(self, step_name: Optional[str] = None) -> None:
        """Generate and log a progress report."""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # Calculate throughput
        if elapsed_time > 0:
            avg_throughput = self.total_processed / elapsed_time
        else:
            avg_throughput = 0
        
        # Format throughput based on tracking unit
        if self.tracking_unit == "rows":
            if avg_throughput >= 1000:
                throughput_str = f"{avg_throughput/1000:.1f}k {self.tracking_unit}/sec"
            else:
                throughput_str = f"{avg_throughput:.0f} {self.tracking_unit}/sec"
        else:
            # For non-row tracking (steps, sources), show simpler throughput
            throughput_str = f"{avg_throughput:.1f} {self.tracking_unit}/sec"
        
        # Only show percentages and ETA if we have a reliable total estimate
        # (i.e., total was provided upfront, not estimated during processing)
        if (self.total_expected and 
            self.total_expected > 0 and 
            hasattr(self, '_total_was_provided_upfront') and 
            self._total_was_provided_upfront):
            
            progress_pct = (self.total_processed / self.total_expected) * 100
            
            # Calculate ETA based on recent throughput
            if self.throughput_history and avg_throughput > 0:
                remaining_rows = self.total_expected - self.total_processed
                eta_seconds = remaining_rows / avg_throughput
                eta_str = self._format_duration(eta_seconds)
                
                if step_name and self.tracking_unit != "rows":
                    self.logger.info(
                        f"⏳ Progress: {self.total_processed}/{self.total_expected} {self.tracking_unit} completed ({progress_pct:.1f}%) | "
                        f"Step '{step_name}' | ETA: {eta_str}"
                    )
                else:
                    self.logger.info(
                        f"⏳ Progress: {self.total_processed:,} {self.tracking_unit} processed ({progress_pct:.1f}%) | "
                        f"{throughput_str} | ETA: {eta_str}"
                    )
            else:
                if step_name and self.tracking_unit != "rows":
                    self.logger.info(
                        f"⏳ Progress: {self.total_processed}/{self.total_expected} {self.tracking_unit} completed ({progress_pct:.1f}%) | "
                        f"Step '{step_name}'"
                    )
                else:
                    self.logger.info(
                        f"⏳ Progress: {self.total_processed:,} {self.tracking_unit} processed ({progress_pct:.1f}%) | "
                        f"{throughput_str}"
                    )
        else:
            # No reliable total expected, just show current progress
            elapsed_str = self._format_duration(elapsed_time)
            if step_name and self.tracking_unit != "rows":
                self.logger.info(
                    f"⏳ Progress: {self.total_processed} {self.tracking_unit} completed | "
                    f"Step '{step_name}' | Elapsed: {elapsed_str}"
                )
            else:
                self.logger.info(
                    f"⏳ Progress: {self.total_processed:,} {self.tracking_unit} processed | "
                    f"{throughput_str} | Elapsed: {elapsed_str}"
                )
    
    def finish(self) -> Dict[str, Any]:
        """
        Complete progress tracking and return summary statistics.
        
        Returns:
            dict: Summary of processing statistics
        """
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        # Calculate final metrics
        avg_throughput = self.total_processed / total_duration if total_duration > 0 else 0
        
        if self.tracking_unit == "rows":
            if avg_throughput >= 1000:
                throughput_str = f"{avg_throughput/1000:.1f}k {self.tracking_unit}/sec"
            else:
                throughput_str = f"{avg_throughput:.0f} {self.tracking_unit}/sec"
        else:
            throughput_str = f"{avg_throughput:.1f} {self.tracking_unit}/sec"
        
        duration_str = self._format_duration(total_duration)
        
        # Log completion message
        if self.tracking_unit == "rows":
            self.logger.info(
                f"✅ {self.table_name} completed: {self.total_processed:,} {self.tracking_unit} in {duration_str} "
                f"(avg: {throughput_str})"
            )
        else:
            self.logger.info(
                f"✅ {self.table_name} completed: {self.total_processed} {self.tracking_unit} in {duration_str} "
                f"(avg: {throughput_str})"
            )
        
        # Return summary statistics
        return {
            'table_name': self.table_name,
            'total_rows': self.total_processed,
            'total_chunks': self.chunks_processed,
            'duration_seconds': total_duration,
            'avg_throughput': avg_throughput,
            'avg_chunk_time': self.avg_chunk_time
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}:{minutes:02d}:{secs:02d}"
    
    def set_total_expected(self, total: int) -> None:
        """Update the expected total rows (useful when total becomes known during processing)."""
        self.total_expected = total
        self.logger.debug(f"Updated expected total for {self.table_name}: {total:,} rows")


def create_progress_tracker(table_name: str,
                          total_expected: Optional[int] = None,
                          chunk_size: int = 50000,
                          verbosity: str = "normal",
                          logger=None) -> ProgressTracker:
    """
    Factory function to create a ProgressTracker with appropriate settings based on verbosity.
    
    Args:
        table_name: Name of operation being processed
        total_expected: Expected total number of rows
        chunk_size: Size of each processing chunk
        verbosity: Verbosity level ("debug", "verbose", "normal", "quiet")
        logger: Logger instance to use
        
    Returns:
        ProgressTracker: Configured progress tracker
    """
    # Set report interval based on verbosity
    if verbosity == "debug":
        report_interval = 1  # Report every chunk
    elif verbosity == "verbose":
        report_interval = 2  # Report every 2 chunks (100k rows)
    elif verbosity == "normal":
        report_interval = 5  # Report every 5 chunks (250k rows)
    else:  # quiet
        report_interval = 10  # Report every 10 chunks (500k rows)
    
    return ProgressTracker(
        total_expected=total_expected,
        table_name=table_name,
        chunk_size=chunk_size,
        report_interval=report_interval,
        logger=logger
    )


__all__ = ['ProgressTracker', 'create_progress_tracker']
