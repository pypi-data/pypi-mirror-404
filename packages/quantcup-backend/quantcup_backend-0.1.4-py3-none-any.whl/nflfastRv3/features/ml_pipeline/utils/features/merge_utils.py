"""Merge Utilities.

Generic data merging utilities with duplicate detection and logging.
Applicable to all ML models that need to merge multiple data sources.

Key Functions:
- safe_merge(): Merge DataFrames with automatic duplicate detection
"""

import pandas as pd
from typing import Union, List, Optional, Tuple, Literal

from commonv2 import get_logger

# Module logger
logger = get_logger(__name__)


class MergeUtils:
    """Generic data merging utilities with duplicate detection."""
    
    @staticmethod
    def safe_merge(
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        on: Union[str, List[str]],
        how: Literal['left', 'right', 'outer', 'inner', 'cross'] = 'left',
        suffixes: Tuple[str, str] = ('', '_right'),
        merge_name: str = "merge"
    ) -> pd.DataFrame:
        """
        Merge DataFrames with automatic duplicate detection and logging.
        
        This utility wraps pandas merge() with comprehensive logging to detect
        and report duplicate keys that could cause row inflation. Critical for
        maintaining data integrity in ML pipelines.
        
        Args:
            left_df: Left DataFrame
            right_df: Right DataFrame
            on: Column(s) to merge on (string or list of strings)
            how: Merge type ('left', 'inner', 'outer', 'right')
            suffixes: Suffixes for overlapping columns (default: ('', '_right'))
            merge_name: Name for logging (e.g., "home features", "contextual")
            
        Returns:
            Merged DataFrame
            
        Example:
            >>> game_df = MergeUtils.safe_merge(
            ...     target_df, features_df,
            ...     on=['game_id', 'season', 'week'],
            ...     merge_name="rolling metrics",
            ...     logger=logger
            ... )
        """
        # Normalize 'on' to list for consistent handling
        merge_cols = on if isinstance(on, list) else [on]
        
        # Log pre-merge state
        logger.info(f"🔍 BEFORE {merge_name}:")
        logger.info(f"   left_df: {len(left_df)} rows, {left_df[merge_cols[0]].nunique()} unique keys")
        logger.info(f"   right_df: {len(right_df)} rows")
        
        # Check for duplicates in right_df (most common source of row inflation)
        right_dupes = right_df.groupby(merge_cols).size()
        right_dupes = right_dupes[right_dupes > 1]
        if len(right_dupes) > 0:
            logger.warning(f"   ⚠️ DUPLICATES in right_df: {len(right_dupes)} keys appear multiple times")
            logger.warning(f"   Sample duplicates: {right_dupes.head().to_dict()}")
        
        # Perform merge
        result_df = left_df.merge(right_df, on=on, how=how, suffixes=suffixes)
        
        logger.info(f"✓ Merged {merge_name}: {len(result_df)} rows")
        
        # Check for duplicates after merge
        merge_cols = on if isinstance(on, list) else [on]
        result_dupes = result_df.groupby(merge_cols[0] if len(merge_cols) == 1 else merge_cols).size()
        result_dupes = result_dupes[result_dupes > 1]
        if len(result_dupes) > 0:
            logger.warning(f"   ⚠️ DUPLICATES after {merge_name}: {len(result_dupes)} keys appear multiple times")
            logger.warning(f"   Sample: {result_dupes.head().to_dict()}")
        
        return result_df


__all__ = ['MergeUtils']