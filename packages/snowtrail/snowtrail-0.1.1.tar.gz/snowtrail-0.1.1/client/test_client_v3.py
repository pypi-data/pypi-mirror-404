"""
Quick test script for v3.1 client updates
Run this after starting the API to verify everything works
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import client
sys.path.insert(0, str(Path(__file__).parent.parent))

from client import Snowtrail

def test_stacks_client():
    """Test stacks client functionality"""
    print("=" * 70)
    print("Testing Stacks Client")
    print("=" * 70)

    client = Snowtrail(base_url="http://127.0.0.1:8001")

    # Test registry
    print("\n1. Testing stack registry...")
    stacks = client.stacks.list_stacks()
    assert len(stacks) > 0, "No stacks found in registry"
    print(f"   [OK] Found {len(stacks)} stack(s)")

    # Test stack info
    print("\n2. Testing stack info...")
    info = client.stacks.get_stack_info("gbsi_us")
    assert info['stack_id'] == 'gbsi_us'
    assert info['current_version'] == '1.0'
    print(f"   [OK] GBSI-US v{info['current_version']} - {info['status']}")

    # Test latest
    print("\n3. Testing latest signal...")
    latest = client.stacks.latest("gbsi_us")
    assert 'gbsi_signal_label' in latest, "Missing v3.1 field: gbsi_signal_label"
    assert 'trade_bias' in latest, "Missing v3.1 field: trade_bias"
    assert 'trade_bias_strength' in latest, "Missing v3.1 field: trade_bias_strength"
    print(f"   [OK] Week {latest['week_ending']}")
    print(f"   [OK] Signal: {latest['gbsi_signal']:.2f} - {latest['gbsi_signal_label']}")
    print(f"   [OK] Trade: {latest['trade_bias_strength']} {latest['trade_bias']}")

    # Test history
    print("\n4. Testing history...")
    df = client.stacks.history("gbsi_us", limit=5)
    assert len(df) > 0, "No history data"
    assert 'gbsi_signal_label' in df.columns
    assert 'trade_bias' in df.columns
    print(f"   [OK] Retrieved {len(df)} rows")

    # Test GBSI convenience methods
    print("\n5. Testing GBSI convenience methods...")
    gbsi = client.stacks.gbsi_us()

    summary = gbsi.latest_summary()
    assert summary['stack_id'] == 'gbsi_us'
    assert 'signal' in summary
    assert 'trade_bias' in summary['signal']
    print(f"   [OK] Summary: {summary['signal']['gbsi_signal_label']}")

    print("\n[PASS] Stacks client tests passed!")


def test_signals_client():
    """Test signals client GBSI v3.1 methods"""
    print("\n" + "=" * 70)
    print("Testing Signals Client GBSI v3.1")
    print("=" * 70)

    client = Snowtrail(base_url="http://127.0.0.1:8001")

    # Test GBSI time series
    print("\n1. Testing GBSI time series...")
    df = client.signals.gbsi_system_stress(limit=5)
    assert len(df) > 0, "No GBSI data"
    assert 'gbsi_signal_label' in df.columns
    assert 'trade_bias' in df.columns
    assert 'trade_bias_strength' in df.columns
    print(f"   [OK] Retrieved {len(df)} rows with v3.1 fields")

    # Test latest structured response
    print("\n2. Testing latest structured response...")
    latest = client.signals.gbsi_system_stress_latest()
    assert 'signal' in latest
    assert 'regime' in latest
    assert 'direction' in latest
    assert 'confidence' in latest
    assert 'components' in latest
    assert latest['signal']['gbsi_signal_label'] is not None
    assert latest['signal']['trade_bias'] is not None
    print(f"   [OK] Signal: {latest['signal']['gbsi_signal_label']}")
    print(f"   [OK] Trade: {latest['signal']['trade_bias_strength']} {latest['signal']['trade_bias']}")
    print(f"   [OK] Confidence: {latest['confidence']['confidence_bucket_label']}")

    print("\n[PASS] Signals client tests passed!")


if __name__ == "__main__":
    try:
        test_stacks_client()
        test_signals_client()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED [PASS]")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        print("\nMake sure the API is running:")
        print("  python -m api.run_api")
        sys.exit(1)
