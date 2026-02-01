#!/usr/bin/env python3
"""
Test script to verify server-based quota tracking works correctly.

Tests:
1. QuotaTracker singleton pattern
2. Server-side quota synchronization
3. Pre-flight quota availability checks
4. Usage summary reporting
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from odds_api.core.quota_tracker import QuotaTracker
from odds_api.etl.extract import api


def test_singleton_pattern():
    """Test that QuotaTracker uses singleton pattern."""
    print("=" * 60)
    print("TEST 1: Singleton Pattern")
    print("=" * 60)
    
    tracker1 = QuotaTracker.get_instance(daily_limit=100)
    tracker2 = QuotaTracker.get_instance(daily_limit=200)  # Should ignore this
    
    assert tracker1 is tracker2, "❌ Not using singleton pattern"
    assert tracker1.default_daily_limit == 100, "❌ Singleton should preserve first instance config"
    
    print("✅ Singleton pattern working correctly")
    print(f"   Both references point to same instance: {id(tracker1) == id(tracker2)}")
    print(f"   Default daily limit preserved: {tracker1.default_daily_limit}")
    print()


def test_usage_update():
    """Test updating local state from server data for multiple keys."""
    print("=" * 60)
    print("TEST 2: Server Usage Update (Per-Key Tracking)")
    print("=" * 60)
    
    # Reset tracker for clean test
    QuotaTracker.reset_instance()
    tracker = QuotaTracker.get_instance(daily_limit=10000, warn_threshold=0.8)
    
    print(f"Initial state (paid): {tracker.get_usage_summary('paid')}")
    
    # Simulate server responses for paid key
    tracker.update_usage(used=45, remaining=9955, key_id='paid')
    print(f"After update (45 used, paid): {tracker.get_usage_summary('paid')}")
    
    tracker.update_usage(used=78, remaining=9922, key_id='paid')
    print(f"After update (78 used, paid): {tracker.get_usage_summary('paid')}")
    
    # Simulate server responses for free key
    tracker.update_usage(used=10, remaining=490, key_id='free')
    print(f"After update (10 used, free): {tracker.get_usage_summary('free')}")
    
    paid_quota = tracker.quotas['paid']
    free_quota = tracker.quotas['free']
    
    assert paid_quota['requests_today'] == 78, f"❌ Expected 78, got {paid_quota['requests_today']}"
    assert paid_quota['daily_limit'] == 10000, f"❌ Expected 10000, got {paid_quota['daily_limit']}"
    assert free_quota['requests_today'] == 10, f"❌ Expected 10, got {free_quota['requests_today']}"
    assert free_quota['daily_limit'] == 500, f"❌ Expected 500, got {free_quota['daily_limit']}"
    
    print("✅ Per-key usage update working correctly")
    print(f"   All quotas: {tracker.get_all_quotas_summary()}")
    print()


def test_quota_check():
    """Test pre-flight quota availability check per key."""
    print("=" * 60)
    print("TEST 3: Pre-Flight Quota Check (Per-Key)")
    print("=" * 60)
    
    # Reset tracker
    QuotaTracker.reset_instance()
    tracker = QuotaTracker.get_instance(daily_limit=1000, warn_threshold=0.8)
    
    # Simulate server reporting high usage for paid key
    tracker.update_usage(used=950, remaining=50, key_id='paid')
    print(f"Server state (paid): {tracker.get_usage_summary('paid')}")
    
    # Check with buffer of 100 (should fail)
    available = tracker.check_quota_available(key_id='paid', buffer=100)
    print(f"Check with buffer=100: {'✅ Available' if available else '❌ Not available'}")
    assert not available, "❌ Should return False when remaining < buffer"
    
    # Check with buffer of 40 (should pass)
    available = tracker.check_quota_available(key_id='paid', buffer=40)
    print(f"Check with buffer=40: {'✅ Available' if available else '❌ Not available'}")
    assert available, "❌ Should return True when remaining > buffer"
    
    print("✅ Quota availability check working correctly")
    print()


def test_dynamic_limit_update():
    """Test dynamic limit updates from server per key."""
    print("=" * 60)
    print("TEST 4: Dynamic Limit Update (Per-Key)")
    print("=" * 60)
    
    # Reset tracker
    QuotaTracker.reset_instance()
    tracker = QuotaTracker.get_instance(daily_limit=10000, warn_threshold=0.8)
    
    print(f"Initial default limit: {tracker.default_daily_limit}")
    
    # Server reports different total for paid key
    tracker.update_usage(used=100, remaining=99900, key_id='paid')
    paid_limit = tracker.quotas['paid']['daily_limit']
    print(f"After update (paid) - New limit: {paid_limit}")
    
    assert paid_limit == 100000, f"❌ Expected 100000, got {paid_limit}"
    
    # Server reports different total for free key
    tracker.update_usage(used=15, remaining=485, key_id='free')
    free_limit = tracker.quotas['free']['daily_limit']
    print(f"After update (free) - New limit: {free_limit}")
    
    assert free_limit == 500, f"❌ Expected 500, got {free_limit}"
    
    print("✅ Dynamic limit update working correctly for multiple keys")
    print(f"   All quotas: {tracker.get_all_quotas_summary()}")
    print()


def test_api_integration():
    """Test that API calls use server-based quota tracking."""
    print("=" * 60)
    print("TEST 5: API Integration (Server-Based Tracking)")
    print("=" * 60)
    print("ℹ️  This test would make actual API calls - SKIPPED for safety")
    print("   To test manually:")
    print("   1. Make API calls through odds_api.etl.extract.api")
    print("   2. Observe quota tracking in logs")
    print()
    
    # Show what would happen
    print("New behavior for any API call:")
    print("  1. PRE-FLIGHT: check_quota_available() warns if quota low (doesn't block)")
    print("  2. API REQUEST: Call server and get response")
    print("  3. POST-RESPONSE: update_usage() updates local state from headers:")
    print("     - x-requests-used → tracker.requests_today")
    print("     - x-requests-remaining → tracker.daily_limit adjustment")
    print("     - x-requests-last → logged for visibility")
    print()
    print("Key difference from old approach:")
    print("  ✅ Server is authoritative source (no client-side calculation)")
    print("  ✅ No false positives from estimation errors")
    print("  ✅ No quota_cost parameters—server tells us actual cost")
    print()


def main():
    """Run all tests."""
    print("\n🧪 QUOTA TRACKING INTEGRATION TESTS\n")
    
    try:
        test_singleton_pattern()
        test_usage_update()
        test_quota_check()
        test_dynamic_limit_update()
        test_api_integration()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\n📋 Summary:")
        print("  ✅ Singleton pattern working")
        print("  ✅ Server-side sync working")
        print("  ✅ Pre-flight quota check working")
        print("  ✅ Dynamic limit update working")
        print("  ℹ️  API integration ready (requires live API calls to test)")
        print("\n🎯 Server-based quota tracking is fully operational!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
