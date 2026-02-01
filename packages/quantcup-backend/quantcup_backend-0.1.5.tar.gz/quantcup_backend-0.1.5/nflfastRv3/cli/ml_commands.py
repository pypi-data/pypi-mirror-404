"""
ML Pipeline CLI Commands

Command-line interface for machine learning operations.

Pattern: Simple command handlers
Complexity: 1 point (basic command routing)
Layer: 1 (Public interface)
"""

import argparse
import logging
from typing import Any, Optional, Dict, cast

from commonv2 import get_logger

# Module-level logger following proper singleton pattern
_logger = get_logger('nflfastRv3.cli.ml')


class MLCommands:
    """ML pipeline command handlers."""
    
    @staticmethod
    def setup_parser(parser: argparse.ArgumentParser) -> None:
        """Setup ML command arguments."""
        subparsers = parser.add_subparsers(dest='ml_command', help='ML operations')
        
        # Feature engineering command
        features_parser = subparsers.add_parser(
            'features',
            help='Engineer features for ML'
        )
        features_parser.add_argument(
            '--seasons',
            type=str,
            help='Optional: Seasons to build features for (e.g., "2020-2023" or "2020,2021,2022"). '
                 'If not provided, builds features for all available seasons in warehouse.'
        )
        features_parser.add_argument(
            '--feature-sets',
            type=str,
            help='Comma-separated list of feature sets to build (e.g., "rolling_metrics,contextual,injury"). '
                 'Available: team_efficiency, rolling_metrics, opponent_adjusted, contextual, injury. '
                 'If not provided, builds all feature sets.'
        )
        features_parser.add_argument(
            '--output-format',
            choices=['console', 'json', 'file'],
            default='console',
            help='Output format'
        )
        
        # Model training command
        train_parser = subparsers.add_parser(
            'train',
            help='Train ML model'
        )
        train_parser.add_argument(
            '--model-name',
            type=str,
            required=True,
            help='Model to train. '
                 'Available: game_outcome, spread_prediction, total_points'
        )
        
        # ========================================
        # TRAINING MODE (RELATIVE YEARS)
        # ========================================
        
        train_parser.add_argument(
            '--train-years',
            type=int,
            help='Number of years to train on before test period (e.g., 5). '
                 'Automatically calculates training window. '
                 'Example: --train-years 5 --test-year 2024 trains on 2019-2023'
        )
        
        train_parser.add_argument(
            '--test-year',
            type=int,
            help='Year to test on (default: current year). '
                 'Used with --train-years for relative training.'
        )
        
        train_parser.add_argument(
            '--test-week',
            type=int,
            help='Specific week to test (1-22, includes playoffs). Tests only that week. '
                 'Example: --test-week 10 tests only week 10 games. '
                 'If not provided, tests on entire year.'
        )
        
        # ========================================
        # v2 FEATURES (NEW)
        # ========================================
        
        train_parser.add_argument(
            '--tag',
            type=str,
            help='Version tag for this model (e.g., "week9_3yr", "baseline"). '
                 'Enables model version tracking and comparison. '
                 'Default: "latest"'
        )
        
        train_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview training configuration without actually training. '
                 'Shows estimated time, memory, and game counts.'
        )

        # Prediction command
        predict_parser = subparsers.add_parser(
            'predict',
            help='Generate predictions using trained model'
        )
        predict_parser.add_argument(
            '--model-name',
            type=str,
            required=True,
            help='Model to use for predictions. '
                 'Available: game_outcome, spread_prediction, total_points'
        )
        predict_parser.add_argument(
            '--version',
            type=str,
            default='latest',
            help='Version tag of trained model to use (default: latest)'
        )
        predict_parser.add_argument(
            '--games',
            type=str,
            help='Comma-separated list of specific game IDs to predict (optional)'
        )
        predict_parser.add_argument(
            '--season',
            type=int,
            help='Season to predict for (default: current season)'
        )
        predict_parser.add_argument(
            '--week',
            type=int,
            help='Week to predict for (default: current week)'
        )
        predict_parser.add_argument(
            '--output-format',
            choices=['console', 'json', 'file'],
            default='console',
            help='Output format for predictions'
        )
        
        # Backtest command - test same config across multiple years
        backtest_parser = subparsers.add_parser(
            'backtest',
            help='Run backtesting across multiple years to test model stability'
        )
        backtest_parser.add_argument(
            '--model-name',
            type=str,
            required=True,
            help='Model to backtest. Available: game_outcome, spread_prediction, total_points'
        )
        backtest_parser.add_argument(
            '--train-years',
            type=int,
            required=True,
            help='Training window size in years (e.g., 5 for 5-year windows)'
        )
        backtest_parser.add_argument(
            '--start-year',
            type=int,
            required=True,
            help='First year to test (e.g., 2020)'
        )
        backtest_parser.add_argument(
            '--end-year',
            type=int,
            required=True,
            help='Last year to test (e.g., 2024)'
        )
        backtest_parser.add_argument(
            '--test-week',
            type=int,
            help='Optional: Specific week to test (1-22). If not provided, tests entire year.'
        )
        
        # Window optimization command - find best training window size
        optimize_parser = subparsers.add_parser(
            'optimize-window',
            help='Find optimal training window size for a specific test period'
        )
        optimize_parser.add_argument(
            '--model-name',
            type=str,
            required=True,
            help='Model to optimize. Available: game_outcome, spread_prediction, total_points'
        )
        optimize_parser.add_argument(
            '--test-year',
            type=int,
            required=True,
            help='Year to test predictions on (e.g., 2025)'
        )
        optimize_parser.add_argument(
            '--test-week',
            type=int,
            required=False,  # ✅ Allow full-season testing
            help='Week to test predictions on (1-22)'
        )
        optimize_parser.add_argument(
            '--min-years',
            type=int,
            default=1,
            help='Minimum training years to test (default: 1)'
        )
        optimize_parser.add_argument(
            '--max-years',
            type=int,
            default=25,
            help='Maximum training years to test (default: 25)'
        )
        optimize_parser.add_argument(
            '--step',
            type=int,
            default=2,
            help='Step size between window sizes (default: 2, tests 1,3,5,7...)'
        )
        
    @staticmethod
    def handle(args: Any, logger: Optional[logging.Logger] = None) -> int:
        """Handle ML commands."""
        logger = logger or _logger
        
        if args.ml_command == 'features':
            return MLCommands._handle_features(args, logger)
        elif args.ml_command == 'train':
            return MLCommands._handle_train(args, logger)
        elif args.ml_command == 'predict':
            return MLCommands._handle_predict(args, logger)
        elif args.ml_command == 'backtest':
            return MLCommands._handle_backtest(args, logger)
        elif args.ml_command == 'optimize-window':
            return MLCommands._handle_optimize_window(args, logger)
        else:
            logger.error("No ML command specified. Use --help for options.")
            return 1
    
    @staticmethod
    def _handle_features(args: Any, logger: Optional[logging.Logger] = None) -> int:
        """Handle feature engineering command."""
        logger = logger or _logger
        
        # Parse seasons argument
        seasons = None
        if args.seasons:
            # Parse season string (e.g., "2020-2023" or "2020,2021,2022")
            if '-' in args.seasons:
                start, end = args.seasons.split('-')
                seasons = list(range(int(start), int(end) + 1))
            else:
                seasons = [int(s.strip()) for s in args.seasons.split(',')]
            
            logger.info(f"🔧 Engineering features for seasons: {seasons}")
        else:
            logger.info("🔧 Engineering features for all available seasons...")
        
        # Parse feature sets argument
        feature_sets = None
        if args.feature_sets:
            from ..features.ml_pipeline.feature_sets import validate_feature_sets, get_available_feature_sets
            
            # Parse comma-separated feature sets
            requested_sets = [fs.strip() for fs in args.feature_sets.split(',')]
            
            # Validate feature sets
            valid_sets, invalid_sets = validate_feature_sets(requested_sets)
            
            if invalid_sets:
                available = get_available_feature_sets()
                logger.error(f"❌ Invalid feature sets: {invalid_sets}")
                logger.error(f"   Available feature sets: {', '.join(available)}")
                return 1
            
            feature_sets = valid_sets
            logger.info(f"🎯 Building feature sets: {', '.join(feature_sets)}")
        else:
            logger.info("🎯 Building all available feature sets...")
        
        try:
            from ..features.ml_pipeline import MLPipelineImpl
            from ..shared.database_router import get_database_router

            # Create ML pipeline and run feature engineering
            db_service = get_database_router()
            ml_pipeline = MLPipelineImpl(db_service, logger)
            
            result = ml_pipeline.build_features_only(
                feature_sets=feature_sets,  # None = all feature sets
                seasons=seasons  # None = all seasons
            )
            
            if result.get('status') == 'success':
                logger.info("✅ Feature engineering complete")
                features_built = result.get('features_built', 0)
                total_rows = result.get('total_rows', 0)
                logger.info(f"Feature sets built: {features_built}")
                logger.info(f"Total rows created: {total_rows:,}")
            else:
                logger.error(f"❌ Feature engineering failed: {result.get('message', 'Unknown error')}")
                return 1
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Feature engineering failed: {e}")
            return 1
    
    @staticmethod
    def _handle_train(args: Any, logger: Optional[logging.Logger] = None) -> int:
        """Handle model training command."""
        logger = logger or _logger
        
        # Validate model name using MODEL_REGISTRY
        from ..features.ml_pipeline.models import validate_models, get_available_models
        
        model_name = args.model_name
        valid_models, invalid_models = validate_models([model_name])
        
        if invalid_models:
            available = get_available_models()
            logger.error(f"❌ Invalid model: {model_name}")
            logger.error(f"   Available models: {', '.join(available)}")
            return 1
        
        logger.info(f"🤖 Training {model_name} model...")
        
        try:
            from ..features.ml_pipeline import create_ml_pipeline
            
            # Use factory - handles db_service initialization
            ml_pipeline = create_ml_pipeline(logger=logger)
            
            # Check for deprecated arguments and show helpful error
            if hasattr(args, 'train_seasons') and args.train_seasons:
                logger.error("❌ --train-seasons is no longer supported.")
                logger.error("   Use --train-years instead for relative training windows.")
                logger.error("   Example: --train-years 5 --test-year 2024")
                return 1
            
            if hasattr(args, 'test_seasons') and args.test_seasons:
                logger.error("❌ --test-seasons is no longer supported.")
                logger.error("   Use --test-year instead for specifying test period.")
                logger.error("   Example: --train-years 5 --test-year 2024")
                return 1
            
            # Collect v2 kwargs (optional features)
            v2_kwargs = {}
            if hasattr(args, 'tag') and args.tag:
                v2_kwargs['tag'] = args.tag
            if hasattr(args, 'dry_run') and args.dry_run:
                v2_kwargs['dry_run'] = args.dry_run
            if hasattr(args, 'auto_build_features'):
                v2_kwargs['auto_build_features'] = args.auto_build_features
            if hasattr(args, 'force') and args.force:
                v2_kwargs['force'] = args.force
            
            # Pass only relative mode args - simplified interface
            result = ml_pipeline.train_model_only(
                model_name=model_name,
                train_years=getattr(args, 'train_years', None),
                test_year=getattr(args, 'test_year', None),
                test_week=getattr(args, 'test_week', None),
                **v2_kwargs
            )
            
            # Handle results
            if result.get('status') in ['success', 'dry_run']:
                logger.info("✅ Model training complete")
                
                # Log metrics if available (not in dry-run)
                if result.get('status') == 'success':
                    metrics = cast(Dict[str, float], result.get('metrics', {}))
                    accuracy = metrics.get('accuracy', 0.0)
                    auc = metrics.get('auc', 0.0)
                    logger.info(f"Model accuracy: {accuracy:.3f}")
                    logger.info(f"Model AUC-ROC: {auc:.3f}")
                    
                    # Generate detailed training report using orchestrator
                    from ..features.ml_pipeline.reporting.orchestrator import ReportOrchestrator
                    report_path = ReportOrchestrator.generate_training_report(result, logger)
                    if report_path:
                        logger.info(f"📊 Training report: {report_path}")
                
                return 0
            else:
                logger.error(f"❌ Model training failed: {result.get('message', 'Unknown error')}")
                return 1
            
        except ValueError as e:
            # Configuration errors (raised by orchestrator)
            logger.error(f"❌ Configuration error: {e}")
            return 1
        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            return 1
    
    @staticmethod
    def _handle_predict(args: Any, logger: Optional[logging.Logger] = None) -> int:
        """Handle prediction command."""
        logger = logger or _logger

        # Validate model name using MODEL_REGISTRY
        from ..features.ml_pipeline.models import validate_models, get_available_models
        
        # model_name is now required by argparse, no default needed
        model_name = args.model_name
        valid_models, invalid_models = validate_models([model_name])
        
        if invalid_models:
            available = get_available_models()
            logger.error(f"❌ Invalid model: {model_name}")
            logger.error(f"   Available models: {', '.join(available)}")
            return 1
        
        logger.info(f"🎯 Using model: {model_name}")

        try:
            from ..features.ml_pipeline import create_ml_pipeline
            
            # Use factory - handles db_service initialization
            ml_pipeline = create_ml_pipeline(logger=logger)
            
            # Pass model_name explicitly (no more hardcoding!)
            result = ml_pipeline.predict(
                model_name=model_name,
                week=getattr(args, 'week', None),
                season=getattr(args, 'season', None),
                model_version=getattr(args, 'version', 'latest')
            )
            
            if result.get('status') != 'success':
                logger.error(f"❌ Prediction failed: {result.get('message', 'Unknown error')}")
                return 1
            
            logger.info("✅ Predictions generated")
            
            # Log report path if generated
            if result.get('report_path'):
                logger.info(f"📊 Report: {result['report_path']}")
            
            # Log summary from enriched result
            predictions = result.get('predictions', [])
            if predictions:
                summary = result.get('summary', {})
                logger.info(f"📋 {summary.get('total_games', 0)} games, "
                           f"{summary.get('high_confidence', 0)} high confidence")
            else:
                logger.warning("⚠️ No predictions generated")
            
            return 0

        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            return 1
    
    @staticmethod
    def _handle_backtest(args: Any, logger: Optional[logging.Logger] = None) -> int:
        """Handle backtesting command - test model across multiple years."""
        logger = logger or _logger
        
        # Validate model name
        from ..features.ml_pipeline.models import validate_models, get_available_models
        
        model_name = args.model_name
        valid_models, invalid_models = validate_models([model_name])
        
        if invalid_models:
            available = get_available_models()
            logger.error(f"❌ Invalid model: {model_name}")
            logger.error(f"   Available models: {', '.join(available)}")
            return 1
        
        logger.info(f"🔬 Backtesting {model_name} from {args.start_year}-{args.end_year}")
        logger.info(f"   Training window: {args.train_years} years")
        if args.test_week:
            logger.info(f"   Testing: Week {args.test_week} only")
        
        try:
            from ..features.ml_pipeline import create_ml_pipeline
            ml_pipeline = create_ml_pipeline(logger=logger)
            
            backtest_results = []
            for test_year in range(args.start_year, args.end_year + 1):
                logger.info(f"\n📊 Testing {test_year}...")
                
                result = ml_pipeline.train_model_only(
                    model_name=model_name,
                    train_years=args.train_years,
                    test_year=test_year,
                    test_week=args.test_week,
                    tag=f"backtest_{test_year}"
                )
                
                if result.get('status') == 'success':
                    metrics = cast(Dict[str, float], result.get('metrics', {}))
                    # Store complete result for aggregated reporting (including X_train/X_test for feature audit)
                    backtest_results.append({
                        'test_year': test_year,
                        'metrics': metrics,
                        'train_size': result.get('train_size', 0),
                        'test_size': result.get('test_size', 0),
                        'train_years': args.train_years,
                        'model': result.get('model'),
                        'X_train': result.get('X_train'),
                        'X_test': result.get('X_test')
                    })
                    logger.info(f"✓ {test_year}: Accuracy={metrics.get('accuracy', 0):.3f}, AUC={metrics.get('auc', 0):.3f}")
                else:
                    logger.warning(f"⚠️  {test_year}: Training failed - {result.get('message', 'Unknown error')}")
            
            if not backtest_results:
                logger.error("❌ No successful results")
                return 1
            
            # Print console summary
            logger.info("\n" + "=" * 60)
            logger.info("BACKTEST RESULTS SUMMARY")
            logger.info("=" * 60)
            for r in backtest_results:
                logger.info(f"{r['test_year']}: Accuracy={r['metrics']['accuracy']:.3f}, AUC={r['metrics']['auc']:.3f}")
            
            avg_acc = sum(r['metrics']['accuracy'] for r in backtest_results) / len(backtest_results)
            avg_auc = sum(r['metrics']['auc'] for r in backtest_results) / len(backtest_results)
            logger.info("=" * 60)
            logger.info(f"AVERAGE: Accuracy={avg_acc:.3f}, AUC={avg_auc:.3f}")
            logger.info(f"Years tested: {len(backtest_results)}/{args.end_year - args.start_year + 1}")
            logger.info("=" * 60)
            
            # Generate aggregated backtest report using orchestrator
            from ..features.ml_pipeline.reporting.orchestrator import ReportOrchestrator
            report_path = ReportOrchestrator.generate_backtest_report(
                backtest_results=backtest_results,
                model_name=model_name,
                train_years=args.train_years,
                start_year=args.start_year,
                end_year=args.end_year,
                test_week=args.test_week,
                logger=logger
            )
            if report_path:
                logger.info(f"\n📊 Detailed backtest report: {report_path}")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Backtesting failed: {e}")
            return 1
    
    @staticmethod
    def _handle_optimize_window(args: Any, logger: Optional[logging.Logger] = None) -> int:
        """Handle window optimization - find best training window size."""
        logger = logger or _logger
        
        # Validate model name
        from ..features.ml_pipeline.models import validate_models, get_available_models
        
        model_name = args.model_name
        valid_models, invalid_models = validate_models([model_name])
        
        if invalid_models:
            available = get_available_models()
            logger.error(f"❌ Invalid model: {model_name}")
            logger.error(f"   Available models: {', '.join(available)}")
            return 1
        
        logger.info(f"🔍 Optimizing training window for {model_name}")
        logger.info(f"   Test: {args.test_year} week {args.test_week}")
        logger.info(f"   Window range: {args.min_years}-{args.max_years} years (step={args.step})")
        
        try:
            from ..features.ml_pipeline import create_ml_pipeline
            ml_pipeline = create_ml_pipeline(logger=logger)
            
            # Multiple random seeds for robust optimization
            random_seeds = [42, 123, 456, 789, 2024]  # 5 seeds for statistical power
            num_seeds = len(random_seeds)
            
            logger.info(f"🎲 Using {num_seeds} random seeds for robust optimization")
            
            optimization_results = []
            for train_years in range(args.min_years, args.max_years + 1, args.step):
                logger.info(f"\n📊 Testing {train_years}-year window...")
                
                # Train with multiple seeds and collect results
                seed_results = []
                for seed_idx, seed in enumerate(random_seeds, 1):
                    logger.info(f"   Iteration {seed_idx}/{num_seeds} (seed={seed})...")
                    
                    result = ml_pipeline.train_model_only(
                        model_name=model_name,
                        train_years=train_years,
                        test_year=args.test_year,
                        test_week=args.test_week,
                        tag=f"window_{train_years}yr_seed{seed}",
                        random_state=seed
                    )
                    
                    if result.get('status') == 'success':
                        seed_results.append(result)
                
                # Aggregate results across seeds
                if seed_results:
                    import numpy as np
                    accuracies = [r['metrics']['accuracy'] for r in seed_results]
                    aucs = [r['metrics']['auc'] for r in seed_results]
                    
                    aggregated_metrics = {
                        'accuracy': float(np.mean(accuracies)),
                        'accuracy_std': float(np.std(accuracies)),
                        'accuracy_min': float(np.min(accuracies)),
                        'accuracy_max': float(np.max(accuracies)),
                        'auc': float(np.mean(aucs)),
                        'auc_std': float(np.std(aucs)),
                    }
                    
                    optimization_results.append({
                        'train_years': train_years,
                        'metrics': aggregated_metrics,
                        'train_size': seed_results[0]['train_size'],
                        'test_size': seed_results[0]['test_size'],
                        'num_seeds': len(seed_results),
                        'X_train': seed_results[0].get('X_train'),
                        'X_test': seed_results[0].get('X_test')
                    })
                    
                    logger.info(
                        f"✓ {train_years} years: {aggregated_metrics['accuracy']:.3f} ± "
                        f"{aggregated_metrics['accuracy_std']:.3f} "
                        f"(range: {aggregated_metrics['accuracy_min']:.3f}-{aggregated_metrics['accuracy_max']:.3f})"
                    )
                else:
                    logger.warning(f"⚠️  {train_years} years: All training iterations failed")
            
            if not optimization_results:
                logger.error("❌ No successful results")
                return 1
            
            # Find best configuration
            best = max(optimization_results, key=lambda x: x['metrics']['accuracy'])
            
            # Print console summary
            logger.info("\n" + "=" * 60)
            logger.info("WINDOW OPTIMIZATION RESULTS")
            logger.info("=" * 60)
            for r in optimization_results:
                marker = " ✨" if r['train_years'] == best['train_years'] else ""
                logger.info(f"{r['train_years']:2d} years: Accuracy={r['metrics']['accuracy']:.3f}, AUC={r['metrics']['auc']:.3f}{marker}")
            logger.info("=" * 60)
            logger.info(f"✨ BEST: {best['train_years']} years (Accuracy={best['metrics']['accuracy']:.3f}, AUC={best['metrics']['auc']:.3f})")
            logger.info(f"Configurations tested: {len(optimization_results)}")
            logger.info("=" * 60)
            
            # Generate aggregated optimization report using orchestrator
            from ..features.ml_pipeline.reporting.orchestrator import ReportOrchestrator
            report_path = ReportOrchestrator.generate_optimization_report(
                optimization_results=optimization_results,
                model_name=model_name,
                test_year=args.test_year,
                test_week=args.test_week,
                min_years=args.min_years,
                max_years=args.max_years,
                logger=logger
            )
            if report_path:
                logger.info(f"\n📊 Detailed optimization report: {report_path}")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Window optimization failed: {e}")
            return 1
