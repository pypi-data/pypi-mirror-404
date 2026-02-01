"""
Checkpoint State Data Structure

Defines the structure for checkpoint state information.

Pattern: Data Class (0 complexity points - pure data structure)
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from datetime import datetime


@dataclass
class CheckpointState:
    """
    Checkpoint state for resumable operations.
    
    Stores progress information for long-running operations to enable
    resume capability after failures or interruptions.
    
    Attributes:
        operation_id: Unique identifier for the operation
        checkpoint_id: Unique identifier for this checkpoint
        created_at: Timestamp when checkpoint was created
        partial_data: Partial results completed so far (serializable)
        items_completed: List of items successfully processed
        items_remaining: List of items still to be processed
        metadata: Additional operation-specific metadata
        storage_key: Key/path where checkpoint is stored
    """
    
    operation_id: str
    checkpoint_id: str
    created_at: datetime
    partial_data: Any = None
    items_completed: List[Any] = field(default_factory=list)
    items_remaining: List[Any] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    storage_key: Optional[str] = None
    
    def to_dict(self) -> dict:
        """
        Convert checkpoint state to dictionary for serialization.
        
        Returns:
            Dict representation of checkpoint state
        """
        return {
            'operation_id': self.operation_id,
            'checkpoint_id': self.checkpoint_id,
            'created_at': self.created_at.isoformat(),
            'items_completed': self.items_completed,
            'items_remaining': self.items_remaining,
            'metadata': self.metadata,
            'storage_key': self.storage_key
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CheckpointState':
        """
        Create checkpoint state from dictionary.
        
        Args:
            data: Dictionary with checkpoint state data
            
        Returns:
            CheckpointState instance
        """
        return cls(
            operation_id=data['operation_id'],
            checkpoint_id=data['checkpoint_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            items_completed=data.get('items_completed', []),
            items_remaining=data.get('items_remaining', []),
            metadata=data.get('metadata', {}),
            storage_key=data.get('storage_key')
        )
    
    def get_progress_percentage(self) -> float:
        """
        Calculate progress percentage.
        
        Returns:
            Progress as percentage (0-100)
        """
        total_items = len(self.items_completed) + len(self.items_remaining)
        if total_items == 0:
            return 100.0
        
        return (len(self.items_completed) / total_items) * 100
    
    def __repr__(self) -> str:
        """String representation of checkpoint state."""
        progress = self.get_progress_percentage()
        return (
            f"CheckpointState(operation_id='{self.operation_id}', "
            f"checkpoint_id='{self.checkpoint_id}', "
            f"progress={progress:.1f}%, "
            f"completed={len(self.items_completed)}, "
            f"remaining={len(self.items_remaining)})"
        )


__all__ = ['CheckpointState']