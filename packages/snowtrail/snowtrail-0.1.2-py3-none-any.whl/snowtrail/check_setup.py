"""
Setup validation for Snowtrail SDK.

Run with: python -m snowtrail.check_setup

Validates:
- Environment variable configuration
- API connectivity
- API key authentication
"""
from __future__ import annotations

import os
import sys


def check_setup() -> bool:
    """
    Validate Snowtrail SDK setup.

    Returns:
        True if all checks pass, False otherwise.
    """
    print("=" * 50)
    print("Snowtrail SDK Setup Check")
    print("=" * 50)
    print()

    all_passed = True

    # Check 1: Environment variable
    print("1. Checking SNOWTRAIL_API_KEY environment variable...")
    api_key = os.environ.get("SNOWTRAIL_API_KEY")
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"   [OK] Found: {masked}")
    else:
        print("   [FAIL] Not set")
        print("   -> Set with: export SNOWTRAIL_API_KEY='your-api-key'")
        all_passed = False
    print()

    # Check 2: Package import
    print("2. Checking package installation...")
    try:
        from snowtrail import Snowtrail, __version__

        print(f"   [OK] snowtrail v{__version__} installed")
    except ImportError as e:
        print(f"   [FAIL] Import failed: {e}")
        print("   -> Install with: pip install snowtrail")
        return False
    print()

    # Check 3: API connectivity (health check - no auth required)
    print("3. Checking API connectivity...")
    try:
        client = Snowtrail()
        health = client.health()
        status = health.get("status", "unknown")
        print(f"   [OK] API reachable (status: {status})")
    except Exception as e:
        print(f"   [FAIL] Connection failed: {e}")
        all_passed = False
    print()

    # Check 4: Authentication (requires valid API key)
    print("4. Checking API authentication...")
    if not api_key:
        print("   [SKIP] No API key set")
    else:
        try:
            from snowtrail import AuthenticationError

            client = Snowtrail(api_key=api_key)
            products = client.products()
            print(f"   [OK] Authenticated ({len(products)} products available)")
        except AuthenticationError as e:
            print(f"   [FAIL] Authentication failed: {e}")
            print("   -> Check that your API key is valid")
            all_passed = False
        except Exception as e:
            print(f"   [FAIL] Request failed: {e}")
            all_passed = False
    print()

    # Check 5: Data access (try fetching latest signal)
    print("5. Checking data access...")
    if not api_key:
        print("   [SKIP] No API key set")
    else:
        try:
            client = Snowtrail(api_key=api_key)
            df = client.gbsi_us.system_stress(latest=True)
            print(f"   [OK] Data access working ({len(df)} rows returned)")
        except Exception as e:
            print(f"   [FAIL] Data fetch failed: {e}")
            all_passed = False
    print()

    # Summary
    print("=" * 50)
    if all_passed:
        print("[OK] All checks passed! SDK is ready to use.")
    else:
        print("[FAIL] Some checks failed. See above for details.")
    print("=" * 50)

    return all_passed


def main() -> None:
    """Entry point for python -m snowtrail.check_setup."""
    success = check_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
