#!/usr/bin/env python3
"""
Complete Play-by-Play Backfill Solution
Downloads all years (1999-2024) and uploads to Sevalla bucket with year partitioning.

This script:
1. Downloads missing years using R (in 5-year chunks to avoid memory issues)
2. Uploads all parquet files to bucket with year partitioning
3. Zero Python memory overhead for uploads

Usage:
    python scripts/complete_pbp_backfill.py
    python scripts/complete_pbp_backfill.py --skip-download  # Only upload existing files
    python scripts/complete_pbp_backfill.py --years 2020-2024  # Download specific range
"""

import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from commonv2.persistence.bucket_adapter import BucketAdapter
from commonv2 import get_logger

# Configuration
OUTPUT_DIR = Path("data/pbp_parquet")
MIN_YEAR = 1999
MAX_YEAR = 2024

# Year ranges for downloading (max 5 years per chunk to avoid memory issues)
YEAR_RANGES = [
    (1999, 2003),
    (2004, 2008),
    (2009, 2013),
    (2014, 2018),
    (2019, 2023),
    (2024, 2024)
]


def get_existing_years(output_dir: Path) -> List[int]:
    """Get list of years that already have parquet files."""
    existing_files = list(output_dir.glob("pbp_*.parquet"))
    existing_years = []
    
    for file in existing_files:
        try:
            year = int(file.stem.split('_')[1])
            existing_years.append(year)
        except (IndexError, ValueError):
            continue
    
    return sorted(existing_years)


def get_missing_year_ranges(existing_years: List[int], 
                           min_year: int = MIN_YEAR, 
                           max_year: int = MAX_YEAR) -> List[Tuple[int, int]]:
    """Determine which year ranges need to be downloaded."""
    all_years = set(range(min_year, max_year + 1))
    missing_years = sorted(all_years - set(existing_years))
    
    if not missing_years:
        return []
    
    # Group missing years into ranges (max 5 years per range)
    ranges = []
    current_start = missing_years[0]
    current_end = missing_years[0]
    
    for year in missing_years[1:]:
        if year == current_end + 1 and (year - current_start) < 5:
            current_end = year
        else:
            ranges.append((current_start, current_end))
            current_start = year
            current_end = year
    
    ranges.append((current_start, current_end))
    return ranges


def download_year_range(start_year: int, end_year: int, output_dir: Path, logger) -> bool:
    """Download play-by-play data for a year range using R."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📦 Downloading years {start_year}-{end_year}...")
    
    r_code = f"""
    suppressPackageStartupMessages({{
      if (!require("nflreadr", quietly=TRUE)) install.packages("nflreadr")
      if (!require("arrow", quietly=TRUE)) install.packages("arrow")
      library(nflreadr); library(arrow)
      options(nflreadr.verbose = FALSE)

      years <- c({', '.join(map(str, range(start_year, end_year + 1)))})
      dir.create("{output_dir}", showWarnings=FALSE, recursive=TRUE)
      
      message("📦 Loading seasons: ", paste(years, collapse=", "))
      
      total_rows <- 0
      for (yr in years) {{
        out_file <- file.path("{output_dir}", sprintf("pbp_%d.parquet", yr))
        if (file.exists(out_file)) {{
          existing_data <- read_parquet(out_file)
          message("✅ Already exists: ", yr, " (", nrow(existing_data), " rows)")
          total_rows <- total_rows + nrow(existing_data)
          next
        }}
        
        message("🔄 Loading ", yr, " ...")
        pbp_year <- load_pbp(seasons = yr, file_type = "parquet")
        write_parquet(pbp_year, out_file)
        total_rows <- total_rows + nrow(pbp_year)
        message("✅ Saved ", yr, ": ", nrow(pbp_year), " rows (Running total: ", total_rows, " rows)")
      }}
      
      message("🎯 Range complete! Total: ", total_rows, " rows")
    }}
    )
    """
    
    try:
        subprocess.run(["Rscript", "-e", r_code], check=True)
        logger.info(f"✅ Downloaded years {start_year}-{end_year}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to download years {start_year}-{end_year}: {e}")
        return False
    except FileNotFoundError:
        logger.error("❌ Rscript not found. Please install R and ensure it's in your PATH")
        return False


def upload_parquet_to_bucket(output_dir: Path, 
                            schema: str = "raw_nflfastr",
                            table: str = "play_by_play",
                            logger=None) -> Tuple[int, int]:
    """
    Upload all parquet files to bucket with year partitioning.
    
    Returns:
        Tuple of (successful_uploads, failed_uploads)
    """
    logger = logger or get_logger('upload_parquet')
    bucket = BucketAdapter(logger=logger)
    
    if not bucket._is_available():
        logger.error("❌ Bucket not available! Check your environment variables:")
        logger.error("   - SEVALLA_BUCKET_NAME or BUCKET_NAME")
        logger.error("   - SEVALLA_BUCKET_ENDPOINT or BUCKET_ENDPOINT_URL")
        logger.error("   - SEVALLA_BUCKET_ACCESS_KEY_ID or AWS_ACCESS_KEY_ID")
        logger.error("   - SEVALLA_BUCKET_SECRET_ACCESS_KEY or AWS_SECRET_ACCESS_KEY")
        return 0, 0
    
    parquet_files = sorted(output_dir.glob("pbp_*.parquet"))
    
    if not parquet_files:
        logger.error(f"❌ No parquet files found in {output_dir}")
        return 0, 0
    
    logger.info(f"📤 Uploading {len(parquet_files)} parquet files to bucket...")
    logger.info(f"   Bucket: {bucket.bucket_name}")
    logger.info(f"   Schema: {schema}")
    logger.info(f"   Table: {table}")
    
    successful = 0
    failed = 0
    
    for file_path in parquet_files:
        try:
            # Extract year from filename (pbp_YYYY.parquet)
            year = int(file_path.stem.split('_')[1])
            
            # Create bucket key with year partitioning (Hive-style)
            bucket_key = f"{schema}/{table}/season={year}/{table}_{year}.parquet"
            
            logger.info(f"📤 Uploading {file_path.name} → {bucket_key}")
            
            success = bucket.upload_file(str(file_path), bucket_key)
            
            if success:
                logger.info(f"✅ Year {year} uploaded successfully")
                successful += 1
            else:
                logger.error(f"❌ Year {year} upload failed")
                failed += 1
                
        except Exception as e:
            logger.error(f"❌ Error uploading {file_path.name}: {e}")
            failed += 1
    
    return successful, failed


def main():
    """Main entry point for complete PBP backfill."""
    parser = argparse.ArgumentParser(
        description="Complete play-by-play backfill: download missing years and upload to bucket"
    )
    parser.add_argument(
        "--skip-download", 
        action="store_true",
        help="Skip download phase, only upload existing files"
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true", 
        help="Skip upload phase, only download files"
    )
    parser.add_argument(
        "--years",
        type=str,
        help="Specific year range to download (e.g., '2020-2024')"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger('complete_pbp_backfill')
    start_time = datetime.now()
    
    logger.info("=" * 70)
    logger.info("COMPLETE PLAY-BY-PLAY BACKFILL")
    logger.info("=" * 70)
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Year range: {MIN_YEAR}-{MAX_YEAR}")
    logger.info("")
    
    # Phase 1: Download missing years
    if not args.skip_download:
        logger.info("📦 PHASE 1: Download Missing Years")
        logger.info("-" * 70)
        
        existing_years = get_existing_years(OUTPUT_DIR)
        logger.info(f"Existing years: {len(existing_years)} files")
        if existing_years:
            logger.info(f"  Years: {min(existing_years)}-{max(existing_years)}")
        
        # Determine which years to download
        if args.years:
            # Parse custom year range
            try:
                start, end = map(int, args.years.split('-'))
                year_ranges = [(start, end)]
                logger.info(f"Custom year range: {start}-{end}")
            except ValueError:
                logger.error(f"Invalid year range format: {args.years}")
                logger.error("Use format: --years 2020-2024")
                return
        else:
            # Auto-detect missing years
            year_ranges = get_missing_year_ranges(existing_years)
        
        if not year_ranges:
            logger.info("✅ All years already downloaded!")
        else:
            logger.info(f"Missing year ranges: {year_ranges}")
            logger.info("")
            
            download_success = 0
            download_failed = 0
            
            for start_year, end_year in year_ranges:
                if download_year_range(start_year, end_year, OUTPUT_DIR, logger):
                    download_success += 1
                else:
                    download_failed += 1
                logger.info("")
            
            logger.info(f"Download summary: {download_success} ranges succeeded, {download_failed} failed")
        
        logger.info("")
    
    # Phase 2: Upload to bucket
    if not args.skip_upload:
        logger.info("📤 PHASE 2: Upload to Bucket")
        logger.info("-" * 70)
        
        successful, failed = upload_parquet_to_bucket(OUTPUT_DIR, logger=logger)
        
        logger.info("")
        logger.info(f"Upload summary: {successful} files succeeded, {failed} failed")
        logger.info("")
    
    # Final summary
    total_time = (datetime.now() - start_time).total_seconds()
    
    logger.info("=" * 70)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 70)
    
    final_years = get_existing_years(OUTPUT_DIR)
    logger.info(f"Total parquet files: {len(final_years)}")
    if final_years:
        logger.info(f"Year coverage: {min(final_years)}-{max(final_years)}")
    logger.info(f"Total time: {total_time:.1f} seconds")
    
    if not args.skip_upload:
        logger.info("")
        logger.info("🎯 Data is now available in bucket with year partitioning:")
        logger.info("   s3://bucket/raw_nflfastr/play_by_play/season=YYYY/play_by_play_YYYY.parquet")
    
    logger.info("=" * 70)


if __name__ == "__main__":
    main()