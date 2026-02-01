from typing import List, Dict, Union, Any, Optional

class FeatureRegistry:
    """
    Central source of truth for all model features.
    Controls which features are active for both training and inference.
    
    This registry prevents the "silent failure" risk where training and inference
    feature lists drift apart. It also serves as documentation for the current
    model configuration and enables programmatic feature selection (ablation studies).
    
    Enhanced with metadata support for institutional memory:
    - Track why features are disabled (correlation, variance, temporal leakage)
    - Record when features were tested
    - Categorize features by type and source
    - Supports both simple bool (legacy) and dict (enhanced) formats
    
    Example enhanced format:
        'qb_time_to_throw_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Extremely low variance (std=0.37)',
            'disabled_date': '2025-12-10',
            'tested_correlation': 0.002,
        }
    """
    
    # Master list of all features with enhanced metadata
    # Format: 'feature_name': {enabled, category, source, [disabled_reason, tested_correlation, etc]}
    # Legacy bool format still supported for backward compatibility
    _FEATURES = {
        # ============================================================================
        # ROLLING DIFFERENTIALS (Core Performance Metrics)
        # Source: rolling_metrics_v1
        # ============================================================================
        
        # --- 4-game rolling windows ---
        'rolling_4g_epa_offense_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_4g_epa_defense_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_4g_point_diff_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_4g_points_for_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_4g_points_against_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_4g_win_rate_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_4g_red_zone_eff_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_4g_third_down_eff_diff': {
            'enabled': False,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'Weak correlation (+0.055)',
            'disabled_date': '2025-11-20',
            'tested_correlation': 0.055,
        },
        'rolling_4g_turnover_diff_diff': {
            'enabled': False,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'Weak correlation (+0.048)',
            'disabled_date': '2025-11-20',
            'tested_correlation': 0.048,
        },
        
        # --- 8-game rolling windows ---
        'rolling_8g_epa_offense_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_8g_epa_defense_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_8g_point_diff_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_8g_points_for_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_8g_points_against_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_8g_win_rate_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_8g_red_zone_eff_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_8g_third_down_eff_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_8g_turnover_diff_diff': {
            'enabled': False,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'Weak correlation (+0.052)',
            'disabled_date': '2025-11-20',
            'tested_correlation': 0.052,
        },
        
        # --- 16-game rolling windows ---
        'rolling_16g_epa_offense_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_16g_epa_defense_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        'rolling_16g_point_diff_diff': {
            'enabled': True,
            'category': 'rolling_differentials',
            'source': 'rolling_metrics_v1',
        },
        
        # ============================================================================
        # RECENT FORM (Momentum Indicators)
        # Source: rolling_metrics_v1
        # ============================================================================
        'recent_4g_win_rate_diff': {
            'enabled': True,
            'category': 'recent_form',
            'source': 'rolling_metrics_v1',
        },
        'recent_4g_avg_margin_diff': {
            'enabled': True,
            'category': 'recent_form',
            'source': 'rolling_metrics_v1',
        },
        'recent_4g_epa_trend_diff': {
            'enabled': True,
            'category': 'recent_form',
            'source': 'rolling_metrics_v1',
        },
        
        # ============================================================================
        # HISTORICAL EFFICIENCY (Stored Game Metrics)
        # Source: rolling_metrics_v1
        # Note: These are stored but not typically used for prediction (use rolling instead)
        # ============================================================================
        'offensive_epa_diff': {
            'enabled': True,
            'category': 'historical_efficiency',
            'source': 'rolling_metrics_v1',
            'notes': 'Stored metric from completed games - use rolling for prediction',
        },
        'defensive_epa_diff': {
            'enabled': True,
            'category': 'historical_efficiency',
            'source': 'rolling_metrics_v1',
            'notes': 'Stored metric from completed games - use rolling for prediction',
        },
        'epa_per_play_offense_diff': {
            'enabled': True,
            'category': 'historical_efficiency',
            'source': 'rolling_metrics_v1',
            'notes': 'Stored metric from completed games - use rolling for prediction',
        },
        'epa_per_play_defense_diff': {
            'enabled': True,
            'category': 'historical_efficiency',
            'source': 'rolling_metrics_v1',
            'notes': 'Stored metric from completed games - use rolling for prediction',
        },
        'red_zone_efficiency_diff': {
            'enabled': True,
            'category': 'historical_efficiency',
            'source': 'rolling_metrics_v1',
            'notes': 'Stored metric from completed games - use rolling for prediction',
        },
        'third_down_efficiency_diff': {
            'enabled': True,
            'category': 'historical_efficiency',
            'source': 'rolling_metrics_v1',
            'notes': 'Stored metric from completed games - use rolling for prediction',
        },
        
        # ============================================================================
        # COMPOSITE FEATURES (Engineered Combinations)
        # Source: feature_synthesis (game_outcome.py)
        # ============================================================================
        'epa_advantage_4game': {
            'enabled': True,
            'category': 'composite',
            'source': 'feature_synthesis',
            'notes': '(Home EPA offense - defense) - (Away EPA offense - defense)',
        },
        'epa_advantage_8game': {
            'enabled': True,
            'category': 'composite',
            'source': 'feature_synthesis',
            'notes': '8-game version of EPA advantage',
        },
        'win_rate_advantage': {
            'enabled': True,
            'category': 'composite',
            'source': 'feature_synthesis',
            'notes': 'Simple differential of recent win rates',
        },
        'momentum_advantage': {
            'enabled': True,
            'category': 'composite',
            'source': 'feature_synthesis',
            'notes': 'Recent EPA trend differential',
        },
        'interaction_form_home': {
            'enabled': True,
            'category': 'composite',
            'source': 'feature_synthesis',
            'notes': 'Multiplicative interaction: Recent form × Stadium advantage',
        },
        'interaction_epa_home': {
            'enabled': True,
            'category': 'composite',
            'source': 'feature_synthesis',
            'notes': 'Multiplicative interaction: EPA advantage × Stadium advantage',
        },
        'interaction_diff_home': {
            'enabled': True,
            'category': 'composite',
            'source': 'feature_synthesis',
            'notes': 'Multiplicative interaction: Point diff × Stadium advantage',
        },
        
        # ============================================================================
        # PHASE 2: NON-LINEAR INTERACTIONS (2025-12-13 REVISED)
        # Source: rolling_metrics_v1 (_create_multiplicative_interactions)
        # Status: ACTIVE - Testing polynomial/threshold/ratio/log transforms
        # Previous Attempt: Simple multiplication failed (all filtered for collinearity >0.90)
        # ============================================================================
        'epa_dome_poly_interaction': {
            'enabled': True,
            'category': 'nonlinear_interaction',
            'source': 'rolling_metrics_v1',
            'phase': 'Phase 2 - Revised',
            'formula': '(epa_differential * is_dome) ** 2',
            'transform': 'polynomial',
            'notes': 'Dome amplifies EPA advantage quadratically. Polynomial creates true non-linearity (correlation <0.90).',
        },
        'conference_threshold_intensity': {
            'enabled': True,
            'category': 'nonlinear_interaction',
            'source': 'rolling_metrics_v1',
            'phase': 'Phase 2 - Revised',
            'formula': '(rolling_4g_point_diff > 3).astype(float) * is_conference_game',
            'transform': 'threshold',
            'notes': 'Rivalry intensity spikes when team is strong (>3 point rolling diff). Threshold creates discrete activation.',
        },
        'rest_performance_ratio': {
            'enabled': True,
            'category': 'nonlinear_interaction',
            'source': 'rolling_metrics_v1',
            'phase': 'Phase 2 - Revised',
            'formula': 'rest_days_diff / (rolling_4g_epa_offense_std + rolling_4g_epa_defense_std + 0.01)',
            'transform': 'ratio',
            'notes': 'Rest advantage relative to performance consistency. Variable denominator (sum of 2 stds) reduces correlation.',
        },
        'stadium_form_log_synergy': {
            'enabled': True,
            'category': 'nonlinear_interaction',
            'source': 'rolling_metrics_v1',
            'phase': 'Phase 2 - Revised',
            'formula': 'log(stadium_home_win_rate * 100 + 1) * recent_4g_win_rate',
            'transform': 'logarithmic',
            'notes': 'Log transform of stadium advantage creates non-linear scaling with recent form.',
        },
        'epa_altitude_threshold': {
            'enabled': True,
            'category': 'nonlinear_interaction',
            'source': 'rolling_metrics_v1',
            'phase': 'Phase 2 - Revised',
            'formula': '(abs(epa_differential) > 0.05).astype(float) * is_high_altitude',
            'transform': 'threshold',
            'notes': 'High altitude impacts become significant only when EPA differential is strong. Optional feature (sparse).',
        },
        
        # ============================================================================
        # PHASE 2: FAILED INTERACTIONS (2025-12-13) - ARCHIVED
        # Source: rolling_metrics_v1 (deprecated implementation)
        # Status: All 4 filtered by Gauntlet Stage 2 - kept for historical reference
        # ============================================================================
        'epa_outdoor_interaction': {
            'enabled': False,
            'category': 'deprecated_interaction',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'DEPRECATED - Filtered by Gauntlet Stage 2. Simple multiplication with binary flag (outdoor_game ∈ {0,1}) creates correlation >0.90 with epa_differential.',
            'disabled_date': '2025-12-13',
            'phase': 'Phase 2 - Failed (Archived)',
            'notes': 'Replaced by epa_dome_poly_interaction (polynomial transform)',
        },
        'venue_form_synergy': {
            'enabled': False,
            'category': 'deprecated_interaction',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'DEPRECATED - Filtered by Gauntlet Stage 2. Simple multiplication creates correlation >0.90 with base features.',
            'disabled_date': '2025-12-13',
            'phase': 'Phase 2 - Failed (Archived)',
            'notes': 'Replaced by stadium_form_log_synergy (logarithmic transform)',
        },
        'grass_epa_interaction': {
            'enabled': False,
            'category': 'deprecated_interaction',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'DEPRECATED - Filtered by Gauntlet Stage 2. Binary multiplication is pseudo-linear.',
            'disabled_date': '2025-12-13',
            'phase': 'Phase 2 - Failed (Archived)',
            'notes': 'Abandoned - no replacement (grass surface interaction not needed)',
        },
        'performance_consistency_index': {
            'enabled': False,
            'category': 'deprecated_interaction',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'DEPRECATED - Filtered by Gauntlet Stage 2. Division by stable std creates correlation >0.90 with numerator.',
            'disabled_date': '2025-12-13',
            'phase': 'Phase 2 - Failed (Archived)',
            'notes': 'Replaced by rest_performance_ratio (variable denominator with sum of 2 stds)',
        },
        
        # ============================================================================
        # CONTEXTUAL - REST
        # Source: contextual_features_v1
        # ============================================================================
        'rest_days_diff': {
            'enabled': True,
            'category': 'contextual_rest',
            'source': 'contextual_features_v1',
        },
        'home_long_rest': {
            'enabled': True,
            'category': 'contextual_rest',
            'source': 'contextual_features_v1',
        },
        'away_long_rest': {
            'enabled': True,
            'category': 'contextual_rest',
            'source': 'contextual_features_v1',
        },
        'home_short_rest': {
            'enabled': False,
            'category': 'contextual_rest',
            'source': 'contextual_features_v1',
            'disabled_reason': 'Unstable/High variance across seasons',
            'disabled_date': '2025-11-15',
        },
        'away_short_rest': {
            'enabled': False,
            'category': 'contextual_rest',
            'source': 'contextual_features_v1',
            'disabled_reason': 'Unstable/High variance across seasons',
            'disabled_date': '2025-11-15',
        },
        
        # ============================================================================
        # CONTEXTUAL - DIVISION/CONFERENCE
        # Source: contextual_features_v1
        # ============================================================================
        'is_division_game': {
            'enabled': False,
            'category': 'contextual_division',
            'source': 'contextual_features_v1',
            'disabled_reason': 'Weak correlation (+0.010)',
            'disabled_date': '2025-11-20',
            'tested_correlation': 0.010,
        },
        'is_conference_game': {
            'enabled': True,
            'category': 'contextual_division',
            'source': 'contextual_features_v1',
        },
        
        # ============================================================================
        # CONTEXTUAL - STADIUM
        # Source: contextual_features_v1
        # ============================================================================
        'stadium_home_win_rate': {
            'enabled': True,
            'category': 'contextual_stadium',
            'source': 'contextual_features_v1',
            'notes': 'Rolling 32-game home win rate by stadium (most predictive contextual feature)',
        },
        'stadium_scoring_rate': {
            'enabled': False,
            'category': 'contextual_stadium',
            'source': 'contextual_features_v1',
            'disabled_reason': 'Poison Pill - High importance but zero correlation (0.000)',
            'disabled_date': '2025-11-09',
            'tested_correlation': 0.000,
        },
        'is_high_altitude': {
            'enabled': True,
            'category': 'contextual_stadium',
            'source': 'contextual_features_v1',
        },
        'is_dome': {
            'enabled': True,
            'category': 'contextual_stadium',
            'source': 'contextual_features_v1',
        },
        'home_site_bias': {
            'enabled': False,
            'category': 'contextual_stadium',
            'source': 'contextual_features_v1',
            'disabled_reason': 'Overfitting risk - passthrough feature',
            'disabled_date': '2025-11-15',
        },
        'is_home_site': {
            'enabled': False,
            'category': 'contextual_stadium',
            'source': 'contextual_features_v1',
            'disabled_reason': 'Overfitting risk - passthrough feature',
            'disabled_date': '2025-11-15',
        },
        
        # ============================================================================
        # CONTEXTUAL - WEATHER (OLD - from contextual_features_v1)
        # Status: DEPRECATED - being replaced by weather_features_v1
        # ============================================================================
        'temp_diff_from_normal': {
            'enabled': False,
            'category': 'contextual_weather_deprecated',
            'source': 'contextual_features_v1',
            'disabled_reason': 'DEPRECATED - Weak correlation (+0.009). Replaced by weather_features_v1',
            'disabled_date': '2025-11-20',
            'tested_correlation': 0.009,
            'deprecated': True,
        },
        'is_precipitation': {
            'enabled': False,
            'category': 'contextual_weather_deprecated',
            'source': 'contextual_features_v1',
            'disabled_reason': 'DEPRECATED - Weak correlation (+0.013). Replaced by precip_keyword_flag in weather_features_v1',
            'disabled_date': '2025-11-20',
            'tested_correlation': 0.013,
            'deprecated': True,
        },
        'high_wind': {
            'enabled': False,
            'category': 'contextual_weather_deprecated',
            'source': 'contextual_features_v1',
            'disabled_reason': 'DEPRECATED - Unstable signal. Replaced by weather_features_v1',
            'disabled_date': '2025-11-15',
            'deprecated': True,
        },
        'weather_passing_impact': {
            'enabled': False,
            'category': 'contextual_weather_deprecated',
            'source': 'contextual_features_v1',
            'disabled_reason': 'DEPRECATED - Temporal leakage. Replaced by weather_features_v1',
            'disabled_date': '2025-11-15',
            'deprecated': True,
        },
        
        # ============================================================================
        # WEATHER FEATURES V1 (2026-01-27)
        # Source: weather_features_v1
        # Strategy: Conservative observables only (no temp differentials until baseline validated)
        # Status: ENABLED for testing - V1 heuristic implementation
        # ============================================================================
        
        # Temperature features
        'temp_raw': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Raw temperature - pass-through from dim_game_weather',
        },
        'is_cold_weather': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Boolean: temp < 32°F (freezing)',
        },
        'is_hot_weather': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Boolean: temp > 85°F',
        },
        'temp_extreme_score': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Normalized distance from 72°F: |temp - 72| / 40',
        },
        
        # Wind features
        'wind_raw': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Raw wind speed - pass-through from dim_game_weather',
        },
        'high_wind': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Boolean: wind > 15 mph (affects passing). Replaces contextual high_wind.',
        },
        'extreme_wind': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Boolean: wind > 20 mph (severe impact)',
        },
        'wind_passing_handicap': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Categorical 0-3: none/moderate/high/extreme wind impact',
        },
        
        # Precipitation features (keyword-based heuristic)
        'precip_keyword_flag': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'UNVALIDATED heuristic: weather string contains precipitation keywords. NOT validated against observed source.',
        },
        'snow_keyword_flag': {
            'enabled': False,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'disabled_reason': 'V1 testing - start with general precip flag only',
            'notes': 'Boolean: weather string contains "snow"',
        },
        'rain_keyword_flag': {
            'enabled': False,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'disabled_reason': 'V1 testing - start with general precip flag only',
            'notes': 'Boolean: weather string contains "rain" or "drizzle"',
        },
        
        # Stadium context (already in contextual_features, but duplicated for weather module)
        'is_outdoor_dim_game': {
            'enabled': False,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'disabled_reason': 'Redundant - already handled by contextual features (is_dome)',
            'notes': 'Boolean: outdoor games that should have weather',
        },
        
        # Composite scores
        'weather_passing_impact': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Negative composite: (precip * -0.05) + (high_wind * -0.08). Replaces contextual version.',
        },
        'weather_rushing_advantage': {
            'enabled': True,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'notes': 'Positive composite: (precip * 0.05) + (high_wind * 0.03). Bad weather favors rushing.',
        },
        'weather_game_environment': {
            'enabled': False,
            'category': 'weather_v1',
            'source': 'weather_features_v1',
            'disabled_reason': 'V1 testing - redundant with passing_impact + rushing_advantage',
            'notes': 'Overall gameplay impact composite',
        },
        
        # ============================================================================
        # CONTEXTUAL - SEASON
        # Source: contextual_features_v1
        # ============================================================================
        'games_remaining': {
            'enabled': False,
            'category': 'contextual_season',
            'source': 'contextual_features_v1',
            'disabled_reason': 'Zero correlation (0.000)',
            'disabled_date': '2025-11-20',
            'tested_correlation': 0.000,
        },
        'is_late_season': {
            'enabled': False,
            'category': 'contextual_season',
            'source': 'contextual_features_v1',
            'disabled_reason': 'Unstable across seasons',
            'disabled_date': '2025-11-15',
        },
        
        # ============================================================================
        # TRENDING DIFFERENTIALS
        # Source: rolling_metrics_v1
        # ============================================================================
        'epa_per_play_offense_trending_diff': {
            'enabled': False,
            'category': 'trending',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'Low correlation with target',
            'disabled_date': '2025-11-15',
        },
        'epa_per_play_defense_trending_diff': {
            'enabled': False,
            'category': 'trending',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'Low correlation with target',
            'disabled_date': '2025-11-15',
        },
        'point_differential_trending_diff': {
            'enabled': False,
            'category': 'trending',
            'source': 'rolling_metrics_v1',
            'disabled_reason': 'Low correlation with target',
            'disabled_date': '2025-11-15',
        },
        
        # ============================================================================
        # INJURY FEATURES (DEPRECATED - 2026-01-25)
        # Source: injury_features_v1 (DEPRECATED MODULE)
        # Status: All disabled - replaced by player_availability_v1
        # Migration: Use player_availability_v1 instead
        # ============================================================================
        # 'home_injury_impact': {
        #     'enabled': False,
        #     'category': 'deprecated_injury',
        #     'source': 'injury_features_v1',
        #     'disabled_reason': 'DEPRECATED - Module replaced by player_availability_v1. Low predictive power / Temporal leakage risk',
        #     'disabled_date': '2026-01-25',
        #     'deprecated': True,
        # },
        # 'away_injury_impact': {
        #     'enabled': False,
        #     'category': 'deprecated_injury',
        #     'source': 'injury_features_v1',
        #     'disabled_reason': 'DEPRECATED - Module replaced by player_availability_v1. Low predictive power / Temporal leakage risk',
        #     'disabled_date': '2026-01-25',
        #     'deprecated': True,
        # },
        # 'injury_impact_diff': {
        #     'enabled': False,
        #     'category': 'deprecated_injury',
        #     'source': 'injury_features_v1',
        #     'disabled_reason': 'DEPRECATED - Module replaced by player_availability_v1. Low variance (std=0.15)',
        #     'disabled_date': '2026-01-25',
        #     'deprecated': True,
        # },
        # 'home_qb_available': {
        #     'enabled': False,
        #     'category': 'deprecated_injury',
        #     'source': 'injury_features_v1',
        #     'disabled_reason': 'DEPRECATED - Replaced by player_availability_v1 (same feature name, better implementation)',
        #     'disabled_date': '2026-01-25',
        #     'deprecated': True,
        #     'notes': 'Feature re-implemented in player_availability_v1 with improved architecture',
        # },
        # 'away_qb_available': {
        #     'enabled': False,
        #     'category': 'deprecated_injury',
        #     'source': 'injury_features_v1',
        #     'disabled_reason': 'DEPRECATED - Replaced by player_availability_v1 (same feature name, better implementation)',
        #     'disabled_date': '2026-01-25',
        #     'deprecated': True,
        #     'notes': 'Feature re-implemented in player_availability_v1 with improved architecture',
        # },
        # 'home_starter_injuries': {
        #     'enabled': False,
        #     'category': 'deprecated_injury',
        #     'source': 'injury_features_v1',
        #     'disabled_reason': 'DEPRECATED - Replaced by home_starter_unavailable in player_availability_v1',
        #     'disabled_date': '2026-01-25',
        #     'deprecated': True,
        # },
        # 'away_starter_injuries': {
        #     'enabled': False,
        #     'category': 'deprecated_injury',
        #     'source': 'injury_features_v1',
        #     'disabled_reason': 'DEPRECATED - Replaced by away_starter_unavailable in player_availability_v1',
        #     'disabled_date': '2026-01-25',
        #     'deprecated': True,
        # },
        
        # ============================================================================
        # PLAYER AVAILABILITY FEATURES (2026-01-25)
        # Source: player_availability_v1
        # Replaces: injury_features_v1 (deprecated)
        # Architecture: Single source (warehouse/player_availability) - cleaner than old injury module
        # ============================================================================
        'home_qb_available': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Binary flag: 1=starting QB available, 0=unavailable. Most critical availability feature.',
        },
        'away_qb_available': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Binary flag: 1=starting QB available, 0=unavailable. Most critical availability feature.',
        },
        'home_starter_unavailable': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Count of unavailable starters across all positions. Replaces home_starter_injuries.',
        },
        'away_starter_unavailable': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Count of unavailable starters across all positions. Replaces away_starter_injuries.',
        },
        'home_offense_unavailable': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Count of unavailable offensive starters (QB, RB, WR, TE, OL).',
        },
        'away_offense_unavailable': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Count of unavailable offensive starters (QB, RB, WR, TE, OL).',
        },
        'home_defense_unavailable': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Count of unavailable defensive starters (DL, LB, DB).',
        },
        'away_defense_unavailable': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Count of unavailable defensive starters (DL, LB, DB).',
        },
        'home_availability_impact': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Position-weighted impact score (sum of position weights for unavailable starters). QB=0.35, key positions weighted.',
        },
        'away_availability_impact': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Position-weighted impact score (sum of position weights for unavailable starters). QB=0.35, key positions weighted.',
        },
        'availability_impact_diff': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Differential: home_availability_impact - away_availability_impact. Positive = home more impacted by unavailability.',
        },
        'player_availability_data_missing': {
            'enabled': True,
            'category': 'player_availability',
            'source': 'player_availability_v1',
            'notes': 'Missing data indicator: 0=data exists, 1=no availability data for this game. Used for data quality monitoring.',
        },
        
        # ============================================================================
        # NEXTGEN QB FEATURES
        # Source: nextgen_features_v1
        # Note: All disabled after Case Study #9 (Feature Dilution)
        # ============================================================================
        'qb_time_to_throw_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Extremely low variance (std=0.37)',
            'disabled_date': '2025-12-10',
            'tested_correlation': 0.002,
        },
        'qb_td_int_ratio_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Low variance (std=1.53)',
            'disabled_date': '2025-12-10',
            'tested_correlation': None,
        },
        'qb_air_yards_to_sticks_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Low variance (std=3.04)',
            'disabled_date': '2025-12-10',
            'tested_correlation': None,
        },
        'qb_completed_air_yards_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Feature dilution - added in batch, decreased accuracy 1.6%',
            'disabled_date': '2025-12-10',
        },
        'qb_attempts_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Feature dilution - added in batch, decreased accuracy 1.6%',
            'disabled_date': '2025-12-10',
        },
        'qb_air_yards_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Feature dilution - added in batch, decreased accuracy 1.6%',
            'disabled_date': '2025-12-10',
        },
        'qb_passer_rating_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Re-test candidate - highest variance NextGen metric',
            'disabled_date': '2025-12-10',
        },
        'qb_completion_pct_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Feature dilution - added in batch, decreased accuracy 1.6%',
            'disabled_date': '2025-12-10',
        },
        'qb_completion_above_exp_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Re-test candidate - NextGen-specific metric',
            'disabled_date': '2025-12-10',
        },
        'qb_aggressiveness_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Feature dilution - added in batch, decreased accuracy 1.6%',
            'disabled_date': '2025-12-10',
        },
        'qb_deep_ball_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Re-test candidate - unique dimension not in rolling averages',
            'disabled_date': '2025-12-10',
        },
        'qb_pass_yards_diff': {
            'enabled': False,
            'category': 'nextgen_qb',
            'source': 'nextgen_features_v1',
            'disabled_reason': 'Feature dilution - added in batch, decreased accuracy 1.6%',
            'disabled_date': '2025-12-10',
        },
    }

    @classmethod
    def get_active_features(cls) -> List[str]:
        """
        Returns list of all currently enabled features.
        
        Supports both legacy bool format and enhanced dict format for backward compatibility.
        """
        active = []
        for name, meta in cls._FEATURES.items():
            if isinstance(meta, dict):
                if meta.get('enabled', False):
                    active.append(name)
            elif meta:  # Legacy bool format
                active.append(name)
        return active

    @classmethod
    def get_all_features(cls) -> List[str]:
        """Returns list of ALL known features (enabled or disabled)."""
        return list(cls._FEATURES.keys())

    @classmethod
    def is_active(cls, feature_name: str) -> bool:
        """
        Check if a specific feature is active.
        
        Supports both legacy bool format and enhanced dict format.
        """
        meta = cls._FEATURES.get(feature_name, False)
        if isinstance(meta, dict):
            return meta.get('enabled', False)
        return bool(meta)
        
    @classmethod
    def set_active(cls, feature_name: str, active: bool):
        """
        Dynamically enable/disable a feature (useful for ablation studies).
        
        Works with both legacy bool and enhanced dict formats.
        """
        if feature_name in cls._FEATURES:
            meta = cls._FEATURES[feature_name]
            if isinstance(meta, dict):
                meta['enabled'] = active
            else:
                cls._FEATURES[feature_name] = active
    
    # ===== Enhanced Metadata Methods =====
    
    @classmethod
    def get_disabled_features(cls) -> Dict[str, Dict]:
        """
        Get all disabled features with their metadata.
        
        Returns:
            dict: Feature name → metadata dict for all disabled features
        """
        disabled = {}
        for name, meta in cls._FEATURES.items():
            if isinstance(meta, dict):
                if not meta.get('enabled', False):
                    disabled[name] = meta
            elif not meta:  # Legacy bool format
                disabled[name] = {'enabled': False, 'category': 'unknown', 'source': 'unknown'}
        return disabled
    
    @classmethod
    def get_features_by_category(cls, category: str, enabled_only: bool = True) -> List[str]:
        """
        Get features by category (e.g., 'rolling_differentials', 'nextgen_qb').
        
        Args:
            category: Feature category to filter by
            enabled_only: If True, only return enabled features
            
        Returns:
            list: Feature names matching the category
        """
        features = []
        for name, meta in cls._FEATURES.items():
            if not isinstance(meta, dict):
                continue
            if meta.get('category') == category:
                if not enabled_only or meta.get('enabled', False):
                    features.append(name)
        return features
    
    @classmethod
    def get_feature_metadata(cls, feature_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific feature.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            dict: Feature metadata (or default dict for legacy bool format)
        """
        meta = cls._FEATURES.get(feature_name)
        if isinstance(meta, dict):
            return meta.copy()
        # Legacy bool format - return minimal metadata
        return {
            'enabled': bool(meta) if meta is not None else False,
            'category': 'unknown',
            'source': 'unknown'
        }
    
    @classmethod
    def get_disabled_summary(cls) -> Dict[str, List[str]]:
        """
        Get summary of why features are disabled (for reports).
        
        Returns:
            dict: Disabled reason → list of feature names
        """
        summary = {}
        for name, meta in cls.get_disabled_features().items():
            reason = meta.get('disabled_reason', 'No reason documented')
            if reason not in summary:
                summary[reason] = []
            summary[reason].append(name)
        return summary
    
    @classmethod
    def get_features_by_source(cls, source: str, enabled_only: bool = True) -> List[str]:
        """
        Get features by data source (e.g., 'rolling_metrics_v1', 'contextual_features_v1').
        
        Args:
            source: Feature source table to filter by
            enabled_only: If True, only return enabled features
            
        Returns:
            list: Feature names from the specified source
        """
        features = []
        for name, meta in cls._FEATURES.items():
            if not isinstance(meta, dict):
                continue
            if meta.get('source') == source:
                if not enabled_only or meta.get('enabled', False):
                    features.append(name)
        return features
    
    @classmethod
    def get_category_summary(cls) -> Dict[str, Dict[str, int]]:
        """
        Get summary of features by category.
        
        Returns:
            dict: Category → {'enabled': count, 'disabled': count}
        """
        summary = {}
        for name, meta in cls._FEATURES.items():
            if isinstance(meta, dict):
                category = meta.get('category', 'unknown')
                enabled = meta.get('enabled', False)
            else:
                category = 'unknown'
                enabled = bool(meta)
            
            if category not in summary:
                summary[category] = {'enabled': 0, 'disabled': 0}
            
            if enabled:
                summary[category]['enabled'] += 1
            else:
                summary[category]['disabled'] += 1
        
        return summary