"""
Checkpointing Utilities for Long-Running Operations

Provides resume capability for long-running operations by saving progress
to S3 bucket storage (with local disk extensibility).

Pattern: Reusable Infrastructure (2 complexity points)
- DI with fallback (1 point)
- Business logic (1 point)

Usage:
    from commonv2.utils.checkpointing import CheckpointManager
    
    # Primary: S3 storage
    manager = CheckpointManager(
        storage_backend='s3',
        bucket_adapter=bucket_adapter,
        max_checkpoints=5  # Retention policy
    )
    
    # Create checkpoint every 5 seasons
    manager.create_checkpoint(
        operation_id='warehouse_play_by_play',
        partial_data=combined_df,
        items_completed=seasons[:i+1],
        items_remaining=seasons[i+1:]
    )
    
    # Resume from checkpoint
    partial_df, remaining = manager.resume('warehouse_play_by_play')
"""

from .manager import CheckpointManager
from .state import CheckpointState

__all__ = ['CheckpointManager', 'CheckpointState']