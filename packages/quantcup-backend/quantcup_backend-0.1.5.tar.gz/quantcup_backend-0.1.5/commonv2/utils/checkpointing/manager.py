"""
Checkpoint Manager for Resumable Operations

Manages checkpoints for long-running operations with S3 storage (primary)
and local disk extensibility (future).

Pattern: Utility Class with DI (2 complexity points)
"""

import os
import io
import json
import tempfile
from typing import Optional, Tuple, Any, List
from datetime import datetime
from uuid import uuid4
import pandas as pd
from ...core.logging import get_logger
from .state import CheckpointState

# Module-level logger
_logger = get_logger('commonv2.utils.checkpointing.manager')


class CheckpointManager:
    """
    Manages checkpoints for resumable operations.
    
    Supports two storage backends:
    - S3 (primary): Durable, survives crashes, accessible from any worker
    - Local disk (future): Faster, but requires manual cleanup
    
    Pattern: Utility Class with DI (2 complexity points)
    - DI with fallback (1 point)
    - Business logic (1 point)
    
    Example:
        >>> # S3 storage (recommended)
        >>> manager = CheckpointManager(
        ...     storage_backend='s3',
        ...     bucket_adapter=bucket_adapter,
        ...     max_checkpoints=5
        ... )
        >>> 
        >>> # Create checkpoint
        >>> manager.create_checkpoint(
        ...     operation_id='warehouse_play_by_play',
        ...     partial_data=combined_df,
        ...     items_completed=seasons[:i+1],
        ...     items_remaining=seasons[i+1:]
        ... )
        >>> 
        >>> # Resume from checkpoint
        >>> partial_df, remaining = manager.resume('warehouse_play_by_play')
    """
    
    def __init__(
        self,
        storage_backend: str = 's3',
        bucket_adapter=None,
        local_path: str = '/tmp/checkpoints',
        max_checkpoints: int = 5,
        logger=None
    ):
        """
        Initialize checkpoint manager.
        
        Args:
            storage_backend: 's3' (default) or 'local'
            bucket_adapter: BucketAdapter instance (required for S3 storage)
            local_path: Local directory path (for local storage)
            max_checkpoints: Maximum checkpoints to keep per operation (default: 5)
            logger: Optional logger instance (uses module logger if not provided)
        """
        self.storage_backend = storage_backend
        self.bucket_adapter = bucket_adapter
        self.local_path = local_path
        self.max_checkpoints = max_checkpoints
        self.logger = logger or _logger
        
        # Validate configuration
        if storage_backend == 's3' and bucket_adapter is None:
            raise ValueError("bucket_adapter required for S3 storage backend")
        
        if storage_backend == 'local':
            os.makedirs(local_path, exist_ok=True)
        
        self.logger.info(
            f"CheckpointManager initialized: backend={storage_backend}, "
            f"max_checkpoints={max_checkpoints}"
        )
    
    def create_checkpoint(
        self,
        operation_id: str,
        partial_data: Any = None,
        items_completed: Optional[List[Any]] = None,
        items_remaining: Optional[List[Any]] = None,
        metadata: Optional[dict] = None
    ) -> CheckpointState:
        """
        Create a checkpoint for an operation.
        
        Args:
            operation_id: Unique identifier for the operation
            partial_data: Partial results (DataFrame, dict, list, etc.)
            items_completed: List of items successfully processed
            items_remaining: List of items still to be processed
            metadata: Additional operation-specific metadata
            
        Returns:
            CheckpointState instance
        """
        checkpoint_id = f"{operation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        
        # Create checkpoint state
        state = CheckpointState(
            operation_id=operation_id,
            checkpoint_id=checkpoint_id,
            created_at=datetime.now(),
            partial_data=partial_data,
            items_completed=items_completed or [],
            items_remaining=items_remaining or [],
            metadata=metadata or {}
        )
        
        # Save checkpoint based on storage backend
        if self.storage_backend == 's3':
            storage_key = self._save_to_s3(state)
        else:
            storage_key = self._save_to_local(state)
        
        state.storage_key = storage_key
        
        # Cleanup old checkpoints
        self.cleanup_old_checkpoints(operation_id)
        
        progress = state.get_progress_percentage()
        self.logger.info(
            f"📍 Checkpoint created: {checkpoint_id} "
            f"({progress:.1f}% complete, {len(state.items_completed)} items done)"
        )
        
        return state
    
    def resume(
        self,
        operation_id: str
    ) -> Tuple[Optional[Any], Optional[List[Any]]]:
        """
        Resume from the most recent checkpoint.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Tuple of (partial_data, items_remaining) or (None, None) if no checkpoint
        """
        # List checkpoints for this operation
        checkpoints = self._list_checkpoints(operation_id)
        
        if not checkpoints:
            self.logger.info(f"No checkpoint found for {operation_id}")
            return None, None
        
        # Get most recent checkpoint
        latest = checkpoints[0]
        
        # Load checkpoint based on storage backend
        if self.storage_backend == 's3':
            state = self._load_from_s3(latest['storage_key'])
        else:
            state = self._load_from_local(latest['storage_key'])
        
        if state is None:
            self.logger.warning(f"Failed to load checkpoint for {operation_id}")
            return None, None
        
        progress = state.get_progress_percentage()
        self.logger.info(
            f"🔄 Resuming from checkpoint: {state.checkpoint_id} "
            f"({progress:.1f}% complete, {len(state.items_remaining)} items remaining)"
        )
        
        return state.partial_data, state.items_remaining
    
    def get_metadata(self, operation_id: str) -> Optional[dict]:
        """
        Get metadata from the most recent checkpoint without loading full data.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Metadata dict or None if no checkpoint exists
        """
        checkpoints = self._list_checkpoints(operation_id)
        
        if not checkpoints:
            return None
        
        # Get most recent checkpoint
        latest = checkpoints[0]
        
        # Load checkpoint state
        if self.storage_backend == 's3':
            state = self._load_from_s3(latest['storage_key'])
        else:
            state = self._load_from_local(latest['storage_key'])
        
        if state is None:
            return None
        
        return state.metadata
    
    def clear_checkpoints(self, operation_id: str):
        """
        Clear all checkpoints for an operation (called on successful completion).
        
        Args:
            operation_id: Unique identifier for the operation
        """
        checkpoints = self._list_checkpoints(operation_id)
        
        for checkpoint in checkpoints:
            self._delete_checkpoint(checkpoint['storage_key'])
        
        self.logger.info(f"🗑️ Cleared {len(checkpoints)} checkpoints for {operation_id}")
    
    def cleanup_old_checkpoints(self, operation_id: str):
        """
        Keep only the N most recent checkpoints per operation.
        
        Args:
            operation_id: Unique identifier for the operation
        """
        checkpoints = self._list_checkpoints(operation_id)
        
        if len(checkpoints) <= self.max_checkpoints:
            return
        
        # Delete checkpoints beyond the max
        for checkpoint in checkpoints[self.max_checkpoints:]:
            self._delete_checkpoint(checkpoint['storage_key'])
            self.logger.debug(f"🗑️ Deleted old checkpoint: {checkpoint['checkpoint_id']}")
    
    def _save_to_s3(self, state: CheckpointState) -> str:
        """Save checkpoint to S3 bucket."""
        try:
            # Create storage key
            storage_key = f"checkpoints/{state.operation_id}/{state.checkpoint_id}.parquet"
            
            # Save metadata as JSON
            metadata_key = f"checkpoints/{state.operation_id}/{state.checkpoint_id}_metadata.json"
            metadata_json = json.dumps(state.to_dict(), indent=2)
            
            self.bucket_adapter.s3_client.put_object(
                Bucket=self.bucket_adapter.bucket_name,
                Key=metadata_key,
                Body=metadata_json.encode('utf-8'),
                ContentType='application/json'
            )
            
            # Save partial data if it's a DataFrame
            if isinstance(state.partial_data, pd.DataFrame):
                parquet_buffer = state.partial_data.to_parquet(index=False, engine='pyarrow')
                self.bucket_adapter.s3_client.put_object(
                    Bucket=self.bucket_adapter.bucket_name,
                    Key=storage_key,
                    Body=parquet_buffer,
                    ContentType='application/octet-stream'
                )
            
            self.logger.debug(f"Saved checkpoint to S3: {storage_key}")
            return storage_key
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint to S3: {e}")
            raise
    
    def _save_to_local(self, state: CheckpointState) -> str:
        """Save checkpoint to local disk."""
        try:
            # Create operation directory
            operation_dir = os.path.join(self.local_path, state.operation_id)
            os.makedirs(operation_dir, exist_ok=True)
            
            # Save metadata
            metadata_path = os.path.join(operation_dir, f"{state.checkpoint_id}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            
            # Save partial data if it's a DataFrame
            if isinstance(state.partial_data, pd.DataFrame):
                data_path = os.path.join(operation_dir, f"{state.checkpoint_id}.parquet")
                state.partial_data.to_parquet(data_path, index=False, engine='pyarrow')
                storage_key = data_path
            else:
                storage_key = metadata_path
            
            self.logger.debug(f"Saved checkpoint to local: {storage_key}")
            return storage_key
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint to local disk: {e}")
            raise
    
    def _load_from_s3(self, storage_key: str) -> Optional[CheckpointState]:
        """Load checkpoint from S3 bucket."""
        try:
            # Load metadata
            metadata_key = storage_key.replace('.parquet', '_metadata.json')
            response = self.bucket_adapter.s3_client.get_object(
                Bucket=self.bucket_adapter.bucket_name,
                Key=metadata_key
            )
            metadata = json.loads(response['Body'].read().decode('utf-8'))
            state = CheckpointState.from_dict(metadata)
            
            # Load partial data if it exists
            try:
                response = self.bucket_adapter.s3_client.get_object(
                    Bucket=self.bucket_adapter.bucket_name,
                    Key=storage_key
                )
                parquet_bytes = response['Body'].read()
                state.partial_data = pd.read_parquet(io.BytesIO(parquet_bytes), engine='pyarrow')
            except Exception:
                # No partial data file (metadata only)
                pass
            
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint from S3: {e}")
            return None
    
    def _load_from_local(self, storage_key: str) -> Optional[CheckpointState]:
        """Load checkpoint from local disk."""
        try:
            # Load metadata
            metadata_path = storage_key.replace('.parquet', '_metadata.json')
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            state = CheckpointState.from_dict(metadata)
            
            # Load partial data if it exists
            if storage_key.endswith('.parquet') and os.path.exists(storage_key):
                state.partial_data = pd.read_parquet(storage_key, engine='pyarrow')
            
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint from local disk: {e}")
            return None
    
    def _list_checkpoints(self, operation_id: str) -> List[dict]:
        """List checkpoints for an operation, sorted by creation time (newest first)."""
        if self.storage_backend == 's3':
            return self._list_checkpoints_s3(operation_id)
        else:
            return self._list_checkpoints_local(operation_id)
    
    def _list_checkpoints_s3(self, operation_id: str) -> List[dict]:
        """List checkpoints from S3."""
        try:
            prefix = f"checkpoints/{operation_id}/"
            response = self.bucket_adapter.s3_client.list_objects_v2(
                Bucket=self.bucket_adapter.bucket_name,
                Prefix=prefix
            )
            
            checkpoints = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('_metadata.json'):
                        checkpoint_id = os.path.basename(obj['Key']).replace('_metadata.json', '')
                        storage_key = obj['Key'].replace('_metadata.json', '.parquet')
                        checkpoints.append({
                            'checkpoint_id': checkpoint_id,
                            'storage_key': storage_key,
                            'created_at': obj['LastModified']
                        })
            
            # Sort by creation time (newest first)
            checkpoints.sort(key=lambda x: x['created_at'], reverse=True)
            return checkpoints
            
        except Exception as e:
            self.logger.error(f"Failed to list S3 checkpoints: {e}")
            return []
    
    def _list_checkpoints_local(self, operation_id: str) -> List[dict]:
        """List checkpoints from local disk."""
        try:
            operation_dir = os.path.join(self.local_path, operation_id)
            if not os.path.exists(operation_dir):
                return []
            
            checkpoints = []
            for filename in os.listdir(operation_dir):
                if filename.endswith('_metadata.json'):
                    checkpoint_id = filename.replace('_metadata.json', '')
                    metadata_path = os.path.join(operation_dir, filename)
                    storage_key = metadata_path.replace('_metadata.json', '.parquet')
                    
                    checkpoints.append({
                        'checkpoint_id': checkpoint_id,
                        'storage_key': storage_key,
                        'created_at': datetime.fromtimestamp(os.path.getmtime(metadata_path))
                    })
            
            # Sort by creation time (newest first)
            checkpoints.sort(key=lambda x: x['created_at'], reverse=True)
            return checkpoints
            
        except Exception as e:
            self.logger.error(f"Failed to list local checkpoints: {e}")
            return []
    
    def _delete_checkpoint(self, storage_key: str):
        """Delete a checkpoint."""
        if self.storage_backend == 's3':
            self._delete_checkpoint_s3(storage_key)
        else:
            self._delete_checkpoint_local(storage_key)
    
    def _delete_checkpoint_s3(self, storage_key: str):
        """Delete checkpoint from S3."""
        try:
            # Delete data file
            self.bucket_adapter.s3_client.delete_object(
                Bucket=self.bucket_adapter.bucket_name,
                Key=storage_key
            )
            
            # Delete metadata file
            metadata_key = storage_key.replace('.parquet', '_metadata.json')
            self.bucket_adapter.s3_client.delete_object(
                Bucket=self.bucket_adapter.bucket_name,
                Key=metadata_key
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to delete S3 checkpoint {storage_key}: {e}")
    
    def _delete_checkpoint_local(self, storage_key: str):
        """Delete checkpoint from local disk."""
        try:
            # Delete data file
            if os.path.exists(storage_key):
                os.remove(storage_key)
            
            # Delete metadata file
            metadata_path = storage_key.replace('.parquet', '_metadata.json')
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
        except Exception as e:
            self.logger.warning(f"Failed to delete local checkpoint {storage_key}: {e}")


def create_checkpoint_manager(
    storage_backend: str = 's3',
    bucket_adapter=None,
    local_path: str = '/tmp/checkpoints',
    max_checkpoints: int = 5,
    logger=None
) -> CheckpointManager:
    """
    Factory function to create checkpoint manager.
    
    Args:
        storage_backend: 's3' (default) or 'local'
        bucket_adapter: BucketAdapter instance (required for S3)
        local_path: Local directory path (for local storage)
        max_checkpoints: Maximum checkpoints to keep per operation
        logger: Optional logger instance
        
    Returns:
        CheckpointManager instance
    """
    return CheckpointManager(
        storage_backend=storage_backend,
        bucket_adapter=bucket_adapter,
        local_path=local_path,
        max_checkpoints=max_checkpoints,
        logger=logger
    )


__all__ = ['CheckpointManager', 'create_checkpoint_manager']