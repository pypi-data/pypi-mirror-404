"""
Variance Analysis Script

Analyzes model prediction variance by Team, Division, and Season Phase.
Used to inform "Variance-Based Gating" strategies.

Usage:
    python scripts/analyze_variance.py --seasons 2022-2024
"""

import sys
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from commonv2.core.logging import get_logger
from nflfastRv3.features.ml_pipeline.orchestrators.model_trainer import create_model_trainer
from nflfastRv3.features.ml_pipeline.models.game_lines.game_outcome import GameOutcomeModel

logger = get_logger(__name__)

def analyze_variance(start_year: int, end_year: int):
    """
    Run variance analysis across multiple seasons.
    """
    logger.info("="*80)
    logger.info(f"VARIANCE ANALYSIS ({start_year}-{end_year})")
    logger.info("="*80)
    
    trainer = create_model_trainer(logger=logger)
    all_predictions = []
    
    # 1. Generate Predictions for each season (Walk-Forward)
    # We use the same logic as validate_weekly but for multiple years
    for year in range(start_year, end_year + 1):
        logger.info(f"\nProcessing {year} season...")
        
        # Train on history up to year-1
        train_seasons = f"2000-{year-1}"
        
        # We need predictions for the WHOLE season to get team-level stats
        # But we must respect walk-forward to avoid leakage.
        # So we iterate through weeks.
        
        cumulative_test_weeks = []
        
        for week in range(1, 23): # Include playoffs
            # Skip if week doesn't exist in data (will be handled by trainer)
            try:
                # Define training data
                if week == 1:
                    train_seasons_str = train_seasons
                    train_weeks = None
                else:
                    train_seasons_str = f"{train_seasons},{year}"
                    train_weeks = {year: cumulative_test_weeks.copy()}
                
                # Train & Predict
                result = trainer.train_model(
                    model_class=GameOutcomeModel,
                    train_seasons=train_seasons_str,
                    train_weeks=train_weeks,
                    test_seasons=str(year),
                    test_week=week,
                    save_model=False,
                    return_predictions=True
                )
                
                if result['status'] == 'success' and 'predictions' in result:
                    preds = result['predictions']
                    preds['season'] = year
                    preds['week'] = week
                    all_predictions.append(preds)
                    cumulative_test_weeks.append(week)
                    print(f"  Week {week}: {len(preds)} games predicted")
                else:
                    # Likely end of season or error
                    pass
                    
            except Exception as e:
                logger.warning(f"  Week {week} failed or no data: {e}")
                continue

    if not all_predictions:
        logger.error("No predictions generated.")
        return

    # Combine all predictions
    df = pd.concat(all_predictions, ignore_index=True)
    logger.info(f"\nTotal Games Analyzed: {len(df)}")
    
    # 2. Calculate Metrics
    # Add correctness flag
    df['correct'] = (df['prediction'] == df['home_team_won']).astype(int)
    df['brier_score'] = (df['home_win_prob'] - df['home_team_won']) ** 2
    
    # --- A. Team Variance ---
    logger.info("\nAnalyzing Team Variance...")
    
    # We need to stack home and away to get per-team stats
    home_df = df[['season', 'week', 'home_team', 'correct', 'brier_score', 'home_win_prob', 'home_team_won']].rename(
        columns={'home_team': 'team', 'home_win_prob': 'win_prob', 'home_team_won': 'won'}
    )
    away_df = df[['season', 'week', 'away_team', 'correct', 'brier_score', 'home_win_prob', 'home_team_won']].rename(
        columns={'away_team': 'team'}
    )
    # For away team, win prob is 1 - home_prob, and won is 1 - home_won
    away_df['win_prob'] = 1 - away_df['home_win_prob']
    away_df['won'] = 1 - away_df['home_team_won']
    
    team_df = pd.concat([home_df, away_df], ignore_index=True)
    
    team_stats = team_df.groupby('team').agg({
        'correct': ['count', 'mean'],
        'brier_score': 'mean'
    })
    team_stats.columns = ['games', 'accuracy', 'brier_score']
    team_stats = team_stats.sort_values('accuracy')
    
    print("\nTop 5 Most Unpredictable Teams (Lowest Accuracy):")
    print(team_stats.head(5))
    
    print("\nTop 5 Most Predictable Teams (Highest Accuracy):")
    print(team_stats.tail(5))
    
    # --- B. Season Phase Variance ---
    logger.info("\nAnalyzing Season Phase Variance...")
    df['phase'] = df['week'].apply(lambda w: 'Early (1-5)' if w <= 5 else 'Late (6+)')
    
    phase_stats = df.groupby('phase').agg({
        'correct': ['count', 'mean'],
        'brier_score': 'mean'
    })
    phase_stats.columns = ['games', 'accuracy', 'brier_score']
    print("\nAccuracy by Phase:")
    print(phase_stats)
    
    # --- C. Team Variance by Phase ---
    # Which teams are specifically hard to predict EARLY?
    team_df['phase'] = team_df['week'].apply(lambda w: 'Early' if w <= 5 else 'Late')
    
    early_team_stats = team_df[team_df['phase'] == 'Early'].groupby('team').agg({
        'correct': ['count', 'mean']
    })
    early_team_stats.columns = ['games', 'accuracy']
    early_team_stats = early_team_stats[early_team_stats['games'] >= 5] # Min sample
    early_team_stats = early_team_stats.sort_values('accuracy')
    
    print("\nMost Unpredictable Teams in EARLY Season (Weeks 1-5):")
    print(early_team_stats.head(5))
    
    # 3. Generate Report
    # Use domain-based subfolder for organization
    # TODO: If generating multiple artifact types (CSV + MD + JSON), consider using
    # timestamped subfolders: Path("reports/variance_analysis") / f"{start_year}_{end_year}_{timestamp}"
    # This groups related artifacts together (see scripts/analyze_pbp_odds_data_v4.py)
    domain_folder = Path("reports") / "variance_analysis"
    domain_folder.mkdir(parents=True, exist_ok=True)
    report_path = domain_folder / f"variance_analysis_{start_year}_{end_year}_{int(time.time())}.md"
    with open(report_path, 'w') as f:
        f.write(f"# Variance Analysis Report ({start_year}-{end_year})\n\n")
        f.write(f"**Total Games:** {len(df)}\n\n")
        
        f.write("## 1. Season Phase Analysis\n")
        f.write(phase_stats.to_markdown())
        f.write("\n\n")
        
        f.write("## 2. Team Variance (Overall)\n")
        f.write(team_stats.to_markdown())
        f.write("\n\n")
        
        f.write("## 3. Early Season Variance (Weeks 1-5)\n")
        f.write("Teams that are notoriously hard to predict early in the season:\n\n")
        f.write(early_team_stats.head(10).to_markdown())
        f.write("\n\n")
        
    logger.info(f"\nReport saved to {report_path}")

if __name__ == "__main__":
    # Default to last 3 years
    analyze_variance(2022, 2024)