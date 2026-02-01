import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from odds_api.utils.schedulers.nfl import NFLScheduler

def test_nfl_scheduler_snapshots():
    cfg = MagicMock()
    cfg.include_week_open_snapshot = True
    cfg.pregame_scheduled_minutes = 15
    cfg.include_in_game_odds = False
    
    scheduler = NFLScheduler(cfg)
    
    game = {
        'id': 'test_game',
        'commence_time': '2023-12-24T18:00:00Z'
    }
    
    snapshots = scheduler.get_snapshots(game)
    
    # Should have 2 snapshots: Open, Pregame Scheduled
    assert len(snapshots) == 2
    
    roles = [s['role'] for s in snapshots]
    assert 'OPEN_T6D' in roles
    assert 'PREGAME_SCHEDULED' in roles

def test_nfl_scheduler_cost_estimation():
    cfg = MagicMock()
    cfg.include_week_open_snapshot = True
    cfg.include_in_game_odds = False
    cfg.pregame_scheduled_minutes = 15
    
    scheduler = NFLScheduler(cfg)
    
    games = [{'id': 'g1'}, {'id': 'g2'}]
    cost = scheduler.estimate_cost(games)
    
    # 2 games * 2 snapshots * 30 credits + 1 schedule = 121
    assert cost['total'] == 121

def test_nfl_scheduler_snapshot_exists():
    cfg = MagicMock()
    cfg.skip_existing_snapshots = True
    cfg.force_refetch = False
    
    scheduler = NFLScheduler(cfg, save_to_bucket=True)
    
    # Mock bucket utilities
    with MagicMock() as mock_list:
        import odds_api.utils.schedulers.nfl as nfl_mod
        nfl_mod.list_odds_files = MagicMock(return_value=['file1.csv'])
        nfl_mod.normalize_timestamp = MagicMock(return_value='20231224T180000Z')
        nfl_mod.extract_date_part = MagicMock(return_value='20231224')
        
        exists = scheduler.snapshot_exists('test_id', '2023-12-24T18:00:00Z', datetime.now(), 'CLOSE')
        assert exists is True

def test_nfl_scheduler_in_game_snapshots():
    cfg = MagicMock()
    cfg.include_week_open_snapshot = False
    cfg.pregame_scheduled_minutes = 15
    cfg.include_in_game_odds = True
    cfg.game_duration_hours = 3
    cfg.max_in_game_snapshots = 5
    cfg.delay_between_snapshots = 0
    
    scheduler = NFLScheduler(cfg)
    
    # Mock API call and crawl
    scheduler.backward_crawl_game_window = MagicMock(return_value=[
        {'timestamp': datetime.now(), 'role': 'IN_GAME', 'snapshot_timestamp': 'ts', 'previous_timestamp': 'prev', 'next_timestamp': 'next', 'game_event': {}}
    ])
    scheduler.snapshot_exists = MagicMock(return_value=False)
    
    game = {
        'id': 'test_game',
        'commence_time': '2023-12-24T18:00:00Z'
    }
    
    snapshots = scheduler.get_snapshots(game)
    
    # 1 Pregame Scheduled + 1 In-Game (mocked)
    assert len(snapshots) == 2
    roles = [s['role'] for s in snapshots]
    assert 'PREGAME_SCHEDULED' in roles
    assert 'IN_GAME' in roles
