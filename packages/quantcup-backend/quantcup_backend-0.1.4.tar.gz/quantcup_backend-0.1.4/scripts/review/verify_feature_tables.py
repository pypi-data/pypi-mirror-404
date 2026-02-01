"""Verification script to check actual columns in all feature tables."""
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger

logger = get_logger('verify_features')
bucket_adapter = get_bucket_adapter(logger=logger)

print("\n" + "="*80)
print("FEATURE TABLE COLUMN VERIFICATION")
print("="*80)

# Feature tables to check
feature_tables = [
    'team_opponent_adjusted_v1',
    'rolling_metrics_v1',
    'team_efficiency_v1'
]

for table_name in feature_tables:
    print(f"\n{'='*80}")
    print(f"TABLE: features/{table_name}")
    print(f"{'='*80}")
    
    try:
        # Read from bucket
        print(f"\n📦 Reading features/{table_name} from bucket...")
        df = bucket_adapter.read_data(table_name, 'features')
        
        if df.empty:
            print(f"⚠️  Table is EMPTY - no data found")
            continue
        
        print(f"✅ Loaded: {len(df):,} rows")
        print(f"✅ Total columns: {len(df.columns)}")
        
        # Check for key columns
        key_columns = ['game_id', 'team', 'season', 'week', 'game_date', 'opponent']
        print(f"\n🔍 Key columns check:")
        print(f"{'Column Name':<20} {'Status':<15} {'Unique Values':<20} {'Sample'}")
        print("-" * 80)
        
        for col in key_columns:
            if col in df.columns:
                unique_count = df[col].nunique()
                sample = df[col].dropna().head(3).tolist()
                sample_str = str(sample)[:30] + "..." if len(str(sample)) > 30 else str(sample)
                print(f"{col:<20} ✅ FOUND         {unique_count:<20} {sample_str}")
            else:
                print(f"{col:<20} ❌ MISSING")
        
        # List all columns
        print(f"\n📋 All {len(df.columns)} columns:")
        for i, col in enumerate(sorted(df.columns), 1):
            dtype = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df) * 100) if len(df) > 0 else 0
            print(f"  {i:3d}. {col:<40} {dtype:<15} (nulls: {null_count:>6} / {null_pct:>5.1f}%)")
        
        # Show sample data
        print(f"\n📊 Sample data (first 3 rows):")
        # Select key columns if they exist
        display_cols = [col for col in ['game_id', 'team', 'season', 'week', 'opponent'] if col in df.columns]
        if display_cols:
            print(df[display_cols].head(3).to_string())
        else:
            print(df.head(3).to_string())
        
        # Check granularity with detailed duplication tracking
        print(f"\n🎯 Data granularity analysis:")
        if 'game_id' in df.columns and 'team' in df.columns:
            game_team_combos = df.groupby(['game_id', 'team']).size()
            max_duplicates = game_team_combos.max()
            total_duplicates = (game_team_combos > 1).sum()
            
            if max_duplicates == 1:
                print(f"  ✅ Game-level: Each (game_id, team) appears once")
                print(f"     Total unique games: {df['game_id'].nunique():,}")
                print(f"     Total unique teams: {df['team'].nunique():,}")
            else:
                print(f"  ⚠️  Multiple rows per (game_id, team)")
                print(f"     Max duplicates for single (game_id, team): {max_duplicates}")
                print(f"     Total (game_id, team) combinations with duplicates: {total_duplicates:,}")
                print(f"     Total rows affected by duplication: {(game_team_combos[game_team_combos > 1].sum() - total_duplicates):,}")
                
                # Show examples of duplicates
                duplicated_combos = game_team_combos[game_team_combos > 1].head(5)
                if len(duplicated_combos) > 0:
                    print(f"\n  📋 Sample duplicated (game_id, team) combinations:")
                    for i in range(len(duplicated_combos)):
                        game_id = duplicated_combos.index[i][0]
                        team = duplicated_combos.index[i][1]
                        count = duplicated_combos.iloc[i]
                        print(f"     {game_id} + {team}: {count} rows")
                        # Show the actual duplicate rows
                        dup_rows = df[(df['game_id'] == game_id) & (df['team'] == team)]
                        if 'week' in dup_rows.columns:
                            print(f"        Weeks: {dup_rows['week'].tolist()}")
                        if 'game_date' in dup_rows.columns:
                            print(f"        Dates: {dup_rows['game_date'].tolist()}")
                
        elif 'team' in df.columns and 'season' in df.columns:
            team_season_combos = df.groupby(['team', 'season']).size()
            max_duplicates = team_season_combos.max()
            total_duplicates = (team_season_combos > 1).sum()
            
            if max_duplicates == 1:
                print(f"  ✅ Team-season level: Each (team, season) appears once")
                print(f"     Total unique teams: {df['team'].nunique():,}")
                print(f"     Total unique seasons: {df['season'].nunique():,}")
            else:
                print(f"  ⚠️  Multiple rows per (team, season)")
                print(f"     Max duplicates for single (team, season): {max_duplicates}")
                print(f"     Total (team, season) combinations with duplicates: {total_duplicates:,}")
                print(f"     Total rows affected by duplication: {(team_season_combos[team_season_combos > 1].sum() - total_duplicates):,}")
                
                # Show examples of duplicates
                duplicated_combos = team_season_combos[team_season_combos > 1].head(5)
                if len(duplicated_combos) > 0:
                    print(f"\n  📋 Sample duplicated (team, season) combinations:")
                    for i in range(len(duplicated_combos)):
                        team = duplicated_combos.index[i][0]
                        season = duplicated_combos.index[i][1]
                        count = duplicated_combos.iloc[i]
                        print(f"     {team} + {season}: {count} rows")
        else:
            print(f"  ⚠️  Cannot determine granularity - missing key columns")
        
    except Exception as e:
        print(f"❌ ERROR reading {table_name}: {e}")

# Summary
print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"\nFeature tables checked: {len(feature_tables)}")
print(f"\n💡 Key findings:")
print(f"  - Check which tables have 'game_id' column")
print(f"  - Check data granularity (game-level vs team-season level)")
print(f"  - Verify if opponent-adjusted features are at the right level")
print(f"\n{'='*80}\n")