#!/usr/bin/env python3
"""
Script to inspect generated predictions in the bucket.
Allows listing recent predictions and viewing their content.
"""

import sys
import os
import argparse
import pandas as pd
import io
from datetime import datetime
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger

# Configure logging
logger = get_logger('inspect_predictions')

def list_prediction_files(bucket_adapter, limit=10):
    """List recent prediction files in the bucket."""
    if not bucket_adapter._is_available():
        logger.error("Bucket not available")
        return []

    try:
        # List objects in ml/predictions/
        # We need to traverse season/week structure
        # This is a simple implementation that lists all and sorts by date
        # For a large bucket, this might need optimization
        
        paginator = bucket_adapter.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(
            Bucket=bucket_adapter.bucket_name,
            Prefix='ml/predictions/'
        )

        files = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith('.parquet'):
                        files.append({
                            'key': key,
                            'last_modified': obj['LastModified'],
                            'size': obj['Size']
                        })

        # Sort by last modified descending
        files.sort(key=lambda x: x['last_modified'], reverse=True)
        return files[:limit]

    except Exception as e:
        logger.error(f"Failed to list prediction files: {e}")
        return []

def read_prediction_file(bucket_adapter, key):
    """Read a prediction file from the bucket."""
    try:
        logger.info(f"Reading {key}...")
        response = bucket_adapter.s3_client.get_object(
            Bucket=bucket_adapter.bucket_name,
            Key=key
        )
        
        # Read parquet content
        content = response['Body'].read()
        df = pd.read_parquet(io.BytesIO(content))
        return df
        
    except Exception as e:
        logger.error(f"Failed to read file {key}: {e}")
        return None

def analyze_predictions(df):
    """Analyze and print prediction details."""
    if df is None or df.empty:
        print("No data found.")
        return

    print("\n" + "="*50)
    print(f"PREDICTION ANALYSIS")
    print("="*50)
    
    print(f"\nTotal Predictions: {len(df)}")
    print(f"Columns: {', '.join(df.columns)}")
    
    print("\nSample Data (First 5 rows):")
    print(df.head().to_string())
    
    if 'home_win_prob' in df.columns:
        print("\nWin Probability Stats:")
        print(df['home_win_prob'].describe())
        
        print("\nWin Probability Distribution:")
        # Bin probabilities
        bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        print(pd.cut(df['home_win_prob'], bins).value_counts().sort_index())

    if 'predicted_winner' in df.columns:
        print("\nPredicted Winners:")
        print(df['predicted_winner'].value_counts())

    if 'confidence' in df.columns:
        print("\nConfidence Stats:")
        print(df['confidence'].describe())

    # Check for explainability features (added in v2 update)
    explainability_cols = [
        'epa_advantage_4game',
        'rolling_4g_epa_offense_diff',
        'rolling_4g_epa_defense_diff',
        'win_rate_advantage',
        'momentum_advantage',
        'rest_days_diff',
        'stadium_home_win_rate'
    ]
    
    available_exp_cols = [col for col in explainability_cols if col in df.columns]
    
    if available_exp_cols:
        print("\nExplainability Features (Sample):")
        # Select game_id, predicted_winner, and available explainability columns
        display_cols = ['game_id', 'predicted_winner'] + available_exp_cols
        print(df[display_cols].head().to_string())
        
        print("\nFeature Stats:")
        print(df[available_exp_cols].describe())

    print("\n" + "="*50)

def main():
    parser = argparse.ArgumentParser(description='Inspect prediction files')
    parser.add_argument('--key', help='Specific bucket key to read')
    parser.add_argument('--latest', action='store_true', help='Read the latest prediction file')
    parser.add_argument('--list', action='store_true', help='List recent prediction files')
    
    args = parser.parse_args()
    
    bucket = get_bucket_adapter()
    
    if args.key:
        df = read_prediction_file(bucket, args.key)
        analyze_predictions(df)
    elif args.list:
        files = list_prediction_files(bucket)
        print("\nRecent Prediction Files:")
        for i, f in enumerate(files):
            print(f"{i+1}. {f['key']} ({f['last_modified']})")
    else:
        # Default behavior: List and ask or read latest if specified
        files = list_prediction_files(bucket)
        
        if not files:
            print("No prediction files found.")
            return

        if args.latest:
            df = read_prediction_file(bucket, files[0]['key'])
            analyze_predictions(df)
        else:
            print("\nRecent Prediction Files:")
            for i, f in enumerate(files):
                print(f"{i+1}. {f['key']} ({f['last_modified']})")
            
            try:
                selection = input("\nEnter number to inspect (or 0 to exit): ")
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(files):
                        df = read_prediction_file(bucket, files[idx]['key'])
                        analyze_predictions(df)
            except KeyboardInterrupt:
                print("\nExiting.")

if __name__ == "__main__":
    main()