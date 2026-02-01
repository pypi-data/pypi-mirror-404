"""
Player ID Mapping Warehouse Transformation

Extracts pfr_player_id ↔ gsis_id crosswalk from players table.

Created: 2026-01-24
Purpose: Enable joining snap_counts (pfr_player_id) with injuries/depth_chart (gsis_id)
Source: raw_nflfastr/players table
"""

import pandas as pd
from commonv2 import get_logger

logger = get_logger(__name__)


def build_player_id_mapping(engine=None, logger_override=None):
    """
    Build player ID mapping table from players table.
    
    Extracts the crosswalk between pfr_player_id (used by snap_counts) and 
    gsis_id (used by injuries, depth_chart, nextgen) from the players table.
    
    This enables Phase 3 of injury features enhancement: joining snap counts 
    with injury/depth chart data using a standardized player ID.
    
    Data Source:
        raw_nflfastr/players table (24,356 rows as of 2026-01-24)
    
    Output Schema:
        - gsis_id: NFL GSIS player ID (e.g., "00-0038389")
        - pfr_player_id: Pro Football Reference ID  (e.g., "AbanIs00")
        - player_name: Display name for debugging (e.g., "Israel Abanikanda")
    
    Args:
        engine: Database engine OR DataFrameEngine (bucket mode) - not used, loads from bucket
        logger_override: Optional logger override
    
    Returns:
        DataFrame with columns: gsis_id, pfr_player_id, player_name
        
    Example:
        >>> mapping = build_player_id_mapping()
        >>> print(len(mapping))
        22000  # ~90% of 24K players have both IDs
    """
    log = logger_override or logger
    
    log.info("📊 Building player_id_mapping from players table...")
    
    # Import bucket adapter
    from commonv2.persistence.bucket_adapter import get_bucket_adapter
    
    bucket_adapter = get_bucket_adapter(logger=log)
    
    try:
        # Load players table from bucket
        players_df = bucket_adapter.read_data('players', 'raw_nflfastr')
        
        if players_df.empty:
            log.warning("⚠️ Players table is empty - cannot build ID mapping")
            return pd.DataFrame(columns=['gsis_id', 'pfr_player_id', 'player_name'])
        
        log.info(f"   Loaded players table: {len(players_df):,} rows")
        
        # Check required columns exist
        required_cols = ['gsis_id', 'pfr_id', 'display_name']
        missing_cols = [col for col in required_cols if col not in players_df.columns]
        
        if missing_cols:
            log.error(f"❌ Missing required columns in players table: {missing_cols}")
            return pd.DataFrame(columns=['gsis_id', 'pfr_player_id', 'player_name'])
        
        # Extract crosswalk columns
        id_mapping = players_df[[
            'gsis_id', 'pfr_id', 'espn_id', 'pff_id', 'nfl_id', 'otc_id', 'display_name'
        ]].copy()
        
        # Rename for consistency with snap_counts table naming
        id_mapping = id_mapping.rename(columns={
            'pfr_id': 'pfr_player_id',
            'display_name': 'player_name'
        })
        
        # Remove rows with missing IDs
        before_filter = len(id_mapping)
        id_mapping = id_mapping.dropna(subset=['gsis_id', 'pfr_player_id'])
        after_filter = len(id_mapping)
        
        filtered_count = before_filter - after_filter
        if filtered_count > 0:
            log.info(f"   Filtered {filtered_count:,} players missing either gsis_id or pfr_player_id")
            log.info(f"   ({(filtered_count/before_filter)*100:.1f}% of total - expected for historical players)")
        
        # Log sample for verification
        if len(id_mapping) > 0:
            sample = id_mapping.head(3)
            log.info(f"   Sample ID mappings:")
            log.info(f"\n{sample.to_string()}")
        
        log.info(f"✓ Built player_id_mapping: {len(id_mapping):,} player records ({(after_filter/before_filter)*100:.1f}% coverage)")
        
        return id_mapping
        
    except Exception as e:
        log.error(f"❌ Failed to build player_id_mapping: {e}", exc_info=True)
        return pd.DataFrame(columns=['gsis_id', 'pfr_player_id', 'player_name'])


__all__ = ['build_player_id_mapping']
