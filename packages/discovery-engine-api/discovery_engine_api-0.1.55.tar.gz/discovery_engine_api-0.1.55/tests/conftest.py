"""
Pytest configuration for Discovery Engine SDK client tests.

This module provides session-level checks and warnings for API key configuration.
"""

import os


def pytest_configure(config):
    """
    Print API key status at the start of the test session.

    This runs once before any tests and provides visibility into whether
    E2E tests will be executed or skipped.
    """
    api_key = os.getenv("DISCOVERY_API_KEY")
    environment = os.getenv("ENVIRONMENT", "staging")

    separator = "=" * 70
    print(f"\n{separator}")
    print("Discovery Engine SDK - E2E Test Configuration")
    print(separator)

    if not api_key:
        print("⚠️  WARNING: DISCOVERY_API_KEY is NOT SET!")
        print("")
        print("   All E2E tests that require the real API will be SKIPPED.")
        print("")
        print("   To enable E2E tests:")
        print("     • In CI: Add DISCOVERY_API_KEY to GitHub Secrets")
        print("     • Locally: export DISCOVERY_API_KEY='disco_...'")
        print("")
    elif not api_key.startswith("disco_"):
        print("⚠️  WARNING: DISCOVERY_API_KEY format appears INVALID!")
        print(f"   Key starts with: '{api_key[:10]}...'")
        print("   Expected format: disco_<token>")
        print("")
        print("   E2E tests may fail with authentication errors.")
        print("")
    else:
        print("✅ DISCOVERY_API_KEY is configured (format looks valid)")
        print(f"✅ Environment: {environment}")
        api_url = (
            "https://leap-labs-production--discovery-api.modal.run"
            if environment == "production"
            else "https://leap-labs-staging--discovery-api.modal.run"
        )
        print(f"✅ API URL: {api_url}")
        print("")

    print(separator)
    print("")
