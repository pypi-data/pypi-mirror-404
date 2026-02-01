"""Quick script to verify dim_game has home_score and away_score columns."""
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger

logger = get_logger('verify_dim_game')
bucket_adapter = get_bucket_adapter(logger=logger)

# Read dim_game from bucket
dim_game = bucket_adapter.read_data('dim_game', 'warehouse')

print(f"\n✅ dim_game loaded: {len(dim_game):,} rows")
print(f"✅ Total columns: {len(dim_game.columns)}")

# ============================================================================
# WEEK 2 2025 SPECIFIC DIAGNOSTIC (for 64-game issue)
# ============================================================================
print(f"\n" + "="*80)
print("WEEK 2 2025 DIAGNOSTIC (64-game issue investigation)")
print("="*80)

if 'season' in dim_game.columns and 'week' in dim_game.columns:
    print(f"\n🔍 Filtering for Week 2 of 2025...")
    week2_2025 = dim_game[(dim_game['season'] == 2025) & (dim_game['week'] == 2)]
    
    print(f"\n📊 Week 2 2025 Summary:")
    print(f"  Total rows: {len(week2_2025)}")
    print(f"  Unique game_ids: {week2_2025['game_id'].nunique()}")
    print(f"  Expected: ~16 rows (one per game)")
    
    if len(week2_2025) == 0:
        print(f"  ⚠️  NO DATA FOUND for Week 2 2025")
    elif len(week2_2025) > 20:
        print(f"  ⚠️  ANOMALY DETECTED: {len(week2_2025)} rows is too many for one week!")
        print(f"     This explains the 64-game test set issue.")
        
        # Check for duplicates
        if 'game_id' in week2_2025.columns:
            game_counts = week2_2025.groupby('game_id').size()
            duplicates = game_counts[game_counts > 1]
            
            if len(duplicates) > 0:
                print(f"\n  🔍 Duplicate Analysis:")
                print(f"     Games with duplicates: {len(duplicates)}")
                print(f"     Max duplicates per game: {game_counts.max()}")
                print(f"\n     Sample duplicates:")
                for game_id, count in duplicates.head(5).items():
                    print(f"       {game_id}: {count} rows")
            else:
                print(f"\n  ℹ️  No duplicate game_ids - each game appears once")
                print(f"     This means there are actually {len(week2_2025)} different games")
    else:
        print(f"  ✅ Row count looks normal")
    
    # Show the actual games
    if len(week2_2025) > 0 and 'home_team' in week2_2025.columns:
        print(f"\n📋 Week 2 2025 Games:")
        display_cols = ['game_id', 'season', 'week', 'home_team', 'away_team']
        if 'home_score' in week2_2025.columns:
            display_cols.extend(['home_score', 'away_score'])
        
        available_cols = [c for c in display_cols if c in week2_2025.columns]
        print(week2_2025[available_cols].to_string(index=False))
else:
    print(f"  ⚠️  Cannot filter - season/week columns not found")

print(f"\n" + "="*80 + "\n")

# Check for duplicates
print(f"\n🔍 Duplication analysis:")
if 'game_id' in dim_game.columns:
    game_counts = dim_game.groupby('game_id').size()
    max_duplicates = game_counts.max()
    total_duplicates = (game_counts > 1).sum()
    unique_games = dim_game['game_id'].nunique()
    
    print(f"  Total rows: {len(dim_game):,}")
    print(f"  Unique game_ids: {unique_games:,}")
    print(f"  Max rows per game_id: {max_duplicates}")
    
    if max_duplicates == 1:
        print(f"  ✅ No duplicates: Each game_id appears exactly once")
    else:
        print(f"  ⚠️  DUPLICATES FOUND!")
        print(f"     Game IDs with duplicates: {total_duplicates:,}")
        print(f"     Total duplicate rows: {(game_counts[game_counts > 1].sum() - total_duplicates):,}")
        
        # Show examples of duplicates
        duplicated_games = game_counts[game_counts > 1].head(10)
        if len(duplicated_games) > 0:
            print(f"\n  📋 Sample duplicated game_ids (showing up to 10):")
            for i in range(len(duplicated_games)):
                game_id = duplicated_games.index[i]
                count = duplicated_games.iloc[i]
                print(f"     {game_id}: {count} rows")
                
                # Show details of duplicate rows
                dup_rows = dim_game[dim_game['game_id'] == game_id]
                if 'play_id' in dup_rows.columns:
                    unique_plays = dup_rows['play_id'].nunique()
                    print(f"        Unique play_ids: {unique_plays}")
                if 'season' in dup_rows.columns and 'week' in dup_rows.columns:
                    print(f"        Season/Week: {dup_rows[['season', 'week']].iloc[0].tolist()}")
else:
    print(f"  ⚠️  Cannot check duplicates - 'game_id' column not found")
print(f"\n📋 Column list:")
for i, col in enumerate(sorted(dim_game.columns), 1):
    print(f"  {i:2d}. {col}")

# Check for score columns
has_home_score = 'home_score' in dim_game.columns
has_away_score = 'away_score' in dim_game.columns

print(f"\n🎯 Score columns check:")
print(f"  home_score: {'✅ FOUND' if has_home_score else '❌ MISSING'}")
print(f"  away_score: {'✅ FOUND' if has_away_score else '❌ MISSING'}")

if has_home_score and has_away_score:
    print(f"\n📊 Sample scores (first 5 games):")
    print(dim_game[['game_id', 'season', 'week', 'home_team', 'away_team', 'home_score', 'away_score']].head())
    
    # Check for null values
    null_home = dim_game['home_score'].isnull().sum()
    null_away = dim_game['away_score'].isnull().sum()
    print(f"\n📈 Data quality:")
    print(f"  Null home_score: {null_home:,} ({null_home/len(dim_game)*100:.1f}%)")
    print(f"  Null away_score: {null_away:,} ({null_away/len(dim_game)*100:.1f}%)")
    print(f"\n✅ SUCCESS: dim_game now has score columns!")
else:
    print(f"\n❌ FAILED: Score columns still missing from dim_game")