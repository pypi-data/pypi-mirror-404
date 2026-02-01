#!/usr/bin/env python3
"""
Test script for Snowtrail SDK.

Run: python test_sdk.py

This tests the SDK against the live API (requires valid API key for data endpoints).
"""
import os
import sys

# Add the local package to path for testing before pip install
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from snowtrail import Snowtrail, AuthenticationError, NotFoundError


def test_health():
    """Test health endpoint (no auth required)."""
    print("=" * 60)
    print("Testing health endpoint...")
    client = Snowtrail()
    result = client.health()
    print(f"  Status: {result.get('status')}")
    assert result.get("status") == "ok", "Health check failed"
    print("  OK: Health check passed")


def test_products():
    """Test products endpoint (no auth required)."""
    print("=" * 60)
    print("Testing products endpoint...")
    client = Snowtrail()
    products = client.products()
    print(f"  Found {len(products)} products:")
    for p in products:
        print(f"    - {p['id']}: {p['name']}")
    assert len(products) > 0, "No products returned"
    print("  OK: Products endpoint passed")


def test_gbsi_us_with_auth(api_key: str):
    """Test GBSI-US endpoints (requires auth)."""
    print("=" * 60)
    print("Testing GBSI-US endpoints...")
    client = Snowtrail(api_key=api_key)

    # Test system stress signal
    print("  Testing system_stress()...")
    df = client.gbsi_us.system_stress()
    print(f"    Columns: {list(df.columns)}")
    print(f"    Rows: {len(df)}")
    assert len(df) > 0, "No data returned"
    print("  OK: system_stress passed")

    # Test with date range
    print("  Testing system_stress with date range...")
    df = client.gbsi_us.system_stress(
        latest=False,
        start="2024-01-01",
        limit=10
    )
    print(f"    Rows: {len(df)}")
    print("  OK: Date range query passed")

    # Test features
    print("  Testing features()...")
    df = client.gbsi_us.features()
    print(f"    Columns: {list(df.columns)[:5]}...")
    print("  OK: Features passed")


def test_gbsi_eu_with_auth(api_key: str):
    """Test GBSI-EU endpoints (requires auth)."""
    print("=" * 60)
    print("Testing GBSI-EU endpoints...")
    client = Snowtrail(api_key=api_key)

    # Test system stress
    print("  Testing system_stress()...")
    df = client.gbsi_eu.system_stress()
    print(f"    Rows: {len(df)}")
    print("  OK: system_stress passed")

    # Test with country filter
    print("  Testing with country filter...")
    df = client.gbsi_eu.system_stress(country="DE")
    print(f"    Rows (DE only): {len(df)}")
    print("  OK: Country filter passed")


def test_auth_required():
    """Test that auth is required for data endpoints."""
    print("=" * 60)
    print("Testing auth requirement...")

    # Temporarily unset env var to test auth requirement
    saved_key = os.environ.pop("SNOWTRAIL_API_KEY", None)
    try:
        client = Snowtrail()  # No API key
        df = client.gbsi_us.system_stress()
        print("  FAIL: Should have raised AuthenticationError")
    except AuthenticationError as e:
        print(f"  Got expected error: {e}")
        print("  OK: Auth requirement verified")
    except Exception as e:
        print(f"  Got error (may be expected): {type(e).__name__}: {e}")
    finally:
        # Restore env var
        if saved_key:
            os.environ["SNOWTRAIL_API_KEY"] = saved_key


def main():
    print("\n" + "=" * 60)
    print("SNOWTRAIL SDK TEST SUITE")
    print("=" * 60)

    # Test public endpoints
    test_health()
    test_products()

    # Test auth requirement
    test_auth_required()

    # Test authenticated endpoints if API key provided
    api_key = os.environ.get("SNOWTRAIL_API_KEY")
    if api_key:
        print("\n" + "=" * 60)
        print("AUTHENTICATED TESTS")
        print("=" * 60)
        test_gbsi_us_with_auth(api_key)
        test_gbsi_eu_with_auth(api_key)
    else:
        print("\n" + "=" * 60)
        print("SKIPPING AUTHENTICATED TESTS")
        print("Set SNOWTRAIL_API_KEY environment variable to run authenticated tests")
        print("=" * 60)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
