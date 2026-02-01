"""Verification script to check actual columns in warehouse/fact_play table."""
from commonv2.persistence.bucket_adapter import get_bucket_adapter
from commonv2 import get_logger

logger = get_logger('verify_fact_play')
bucket_adapter = get_bucket_adapter(logger=logger)

print("\n" + "="*80)
print("WAREHOUSE TABLE COLUMN VERIFICATION")
print("="*80)

# Read fact_play from warehouse bucket
print("\n📦 Reading warehouse/fact_play from bucket...")
fact_play = bucket_adapter.read_data('fact_play', 'warehouse')

print(f"✅ fact_play loaded: {len(fact_play):,} rows")
print(f"✅ Total columns: {len(fact_play.columns)}")

# Check for critical columns needed by feature engineering
critical_columns = [
    'play_id', 'game_id', 'season', 'week',
    'posteam', 'defteam', 'play_type', 'epa',
    'yardline_100', 'down', 'ydstogo', 'yards_gained',
    'touchdown', 'interception', 'fumble_lost',
    'rush_attempt', 'pass_attempt', 'third_down_conv'
]

print(f"\n🔍 Checking critical columns for feature engineering:")
print(f"{'Column Name':<25} {'Status':<15} {'Sample Values'}")
print("-" * 80)

missing_columns = []
for col in critical_columns:
    if col in fact_play.columns:
        # Get sample non-null values
        sample = fact_play[col].dropna().head(3).tolist()
        sample_str = str(sample)[:40] + "..." if len(str(sample)) > 40 else str(sample)
        print(f"{col:<25} ✅ FOUND         {sample_str}")
    else:
        print(f"{col:<25} ❌ MISSING")
        missing_columns.append(col)

# List all actual columns
print(f"\n📋 All {len(fact_play.columns)} columns in fact_play:")
for i, col in enumerate(sorted(fact_play.columns), 1):
    print(f"  {i:3d}. {col}")

# Check for alternative column names
print(f"\n🔎 Searching for alternative column names:")
alternative_patterns = {
    'fumble_lost': ['fumble', 'fumble_recovery', 'fumble_lost'],
    'touchdown': ['td', 'touchdown', 'score'],
    'interception': ['int', 'interception', 'pass_int']
}

for expected, patterns in alternative_patterns.items():
    print(f"\n  Looking for '{expected}':")
    found = []
    for col in fact_play.columns:
        for pattern in patterns:
            if pattern.lower() in col.lower():
                found.append(col)
                break
    if found:
        print(f"    ✅ Found alternatives: {found}")
    else:
        print(f"    ❌ No alternatives found")

# Summary
print(f"\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Total columns in fact_play: {len(fact_play.columns)}")
print(f"Critical columns checked: {len(critical_columns)}")
print(f"Missing columns: {len(missing_columns)}")
if missing_columns:
    print(f"\n❌ MISSING COLUMNS:")
    for col in missing_columns:
        print(f"  - {col}")
    print(f"\n⚠️  These columns need to be added to WAREHOUSE_COLUMN_REQUIREMENTS")
else:
    print(f"\n✅ All critical columns present!")

print("="*80 + "\n")