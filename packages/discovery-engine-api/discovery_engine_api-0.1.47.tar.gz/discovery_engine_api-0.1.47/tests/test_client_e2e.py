"""
End-to-end tests for the Discovery Engine Python SDK.

These tests call the real API and exercise the full flow including Modal.
They are skipped if API credentials are not available.

To run these tests locally:
    # Set required environment variables
    export DISCOVERY_API_KEY="your-api-key"

    # Optional: Set environment (defaults to staging)
    export ENVIRONMENT="staging"  # or "production"

    # Run e2e tests
    pytest engine/packages/client/tests/test_client_e2e.py -v

    # Or run all tests except e2e
    pytest -m "not e2e"

To run in CI (GitHub Actions):
    Set these secrets in GitHub:
    - DISCOVERY_API_KEY: Your API key
    - ENVIRONMENT: "staging" or "production" (optional, defaults to staging)

    The tests will:
    - Auto-detect environment from ENVIRONMENT or VERCEL_ENV
    - Use staging URL (https://leap-labs-staging--discovery-api.modal.run) by default
    - Use production URL (https://leap-labs-production--discovery-api.modal.run) if ENVIRONMENT=production
    - Skip gracefully if DISCOVERY_API_KEY is not set
"""

import io
import os
import sys

import pandas as pd
import pytest

# Test data - simple regression dataset
TEST_DATA_CSV = """age,income,experience,price
25,50000,2,150000
30,60000,5,180000
35,70000,8,220000
40,80000,12,250000
45,90000,15,280000
28,55000,3,160000
32,65000,6,190000
38,75000,10,230000
42,85000,13,260000
48,95000,18,300000
"""


# Hardcoded API URLs (Modal-hosted FastAPI backend)
STAGING_API_URL = "https://leap-labs-staging--discovery-api.modal.run"
PRODUCTION_API_URL = "https://leap-labs-production--discovery-api.modal.run"


def get_api_key() -> str | None:
    """Get API key from environment variable."""
    return os.getenv("DISCOVERY_API_KEY")


def validate_api_key_format(api_key: str) -> tuple[bool, str]:
    """
    Validate that the API key has the expected format.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key:
        return False, "API key is empty"

    if not api_key.startswith("disco_"):
        return False, f"API key should start with 'disco_', got: '{api_key[:10]}...'"

    # Expected format: disco_<base64-like-string>
    # Should be at least 20 characters total
    if len(api_key) < 20:
        return False, f"API key appears too short ({len(api_key)} chars)"

    return True, ""


def print_api_key_warning(message: str) -> None:
    """Print a loud warning about API key issues."""
    separator = "=" * 70
    print(f"\n{separator}", file=sys.stderr)
    print("⚠️  WARNING: DISCOVERY_API_KEY ISSUE", file=sys.stderr)
    print(separator, file=sys.stderr)
    print(f"  {message}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  E2E tests against the real API will be SKIPPED.", file=sys.stderr)
    print("", file=sys.stderr)
    print("  To fix this:", file=sys.stderr)
    print("    1. Get a valid API key from the Discovery dashboard", file=sys.stderr)
    print("    2. Set it in GitHub: Settings → Secrets → DISCOVERY_API_KEY", file=sys.stderr)
    print("    3. Or locally: export DISCOVERY_API_KEY='disco_...'", file=sys.stderr)
    print(f"{separator}\n", file=sys.stderr)


def get_environment() -> str:
    """
    Determine the current environment (staging or production).

    Checks environment variables in order:
    1. ENVIRONMENT (set in CI/GitHub Actions)
    2. VERCEL_ENV (set in Vercel deployments)
    3. Defaults to staging
    """
    env = os.getenv("ENVIRONMENT") or os.getenv("VERCEL_ENV")
    if env == "production":
        return "production"
    return "staging"


def get_api_url() -> str:
    """
    Get API URL based on environment.

    Returns:
        - Production URL if environment is production
        - Staging URL otherwise (default)
    """
    env = get_environment()
    if env == "production":
        return PRODUCTION_API_URL
    return STAGING_API_URL


@pytest.fixture
def api_key():
    """Get API key from environment, skip test if not available or invalid."""
    key = get_api_key()

    if not key:
        print_api_key_warning("DISCOVERY_API_KEY environment variable is NOT SET")
        pytest.skip("DISCOVERY_API_KEY environment variable not set")

    is_valid, error_message = validate_api_key_format(key)
    if not is_valid:
        print_api_key_warning(f"DISCOVERY_API_KEY format is INVALID: {error_message}")
        pytest.skip(f"DISCOVERY_API_KEY format invalid: {error_message}")

    return key


@pytest.fixture
def api_url():
    """Get API URL from environment (optional)."""
    return get_api_url()


@pytest.fixture
def test_dataframe():
    """Create test DataFrame from CSV string."""
    try:
        return pd.read_csv(io.StringIO(TEST_DATA_CSV))
    except ImportError:
        pytest.skip("pandas not available")


@pytest.fixture
def engine(api_key, api_url):
    """Create Engine instance with API key and optional URL."""
    from discovery import Engine

    engine = Engine(api_key=api_key)
    if api_url:
        engine.base_url = api_url.rstrip("/")
    return engine


def print_auth_error_warning(error: Exception, api_url: str) -> None:
    """Print a loud warning about authentication failures."""
    separator = "=" * 70
    print(f"\n{separator}", file=sys.stderr)
    print("❌ ERROR: API AUTHENTICATION FAILED", file=sys.stderr)
    print(separator, file=sys.stderr)
    print(f"  API URL: {api_url}", file=sys.stderr)
    print(f"  Error: {error}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  This usually means:", file=sys.stderr)
    print("    • The DISCOVERY_API_KEY is invalid or expired", file=sys.stderr)
    print("    • The key doesn't have permission for this environment", file=sys.stderr)
    print("", file=sys.stderr)
    print("  To fix this:", file=sys.stderr)
    print("    1. Get a new API key from the Discovery dashboard", file=sys.stderr)
    print("    2. Update the DISCOVERY_API_KEY secret in GitHub", file=sys.stderr)
    print(f"{separator}\n", file=sys.stderr)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_client_e2e_full_flow(engine, test_dataframe, api_url):
    """
    Test the full end-to-end flow: upload, analyze, wait for completion.

    This test:
    1. Uploads a test dataset via the API
    2. Creates a run
    3. Waits for Modal to process the job
    4. Verifies results are returned

    This exercises the complete production flow including Modal.
    """
    try:
        # Run analysis with wait=True to exercise full flow including Modal
        result = await engine.run_async(
            file=test_dataframe,
            target_column="price",
            depth_iterations=1,
            description="E2E test dataset - house price prediction",
            column_descriptions={
                "age": "Age of the property owner",
                "income": "Annual income in USD",
                "experience": "Years of work experience",
                "price": "House price in USD",
            },
            auto_report_use_llm_evals=False,  # Disable LLMs for faster test
            wait=True,  # Wait for completion (exercises Modal)
            wait_timeout=600,  # 10 minute timeout
        )
    except Exception as e:
        error_str = str(e).lower()
        if (
            "401" in error_str
            or "403" in error_str
            or "unauthorized" in error_str
            or "forbidden" in error_str
        ):
            print_auth_error_warning(e, api_url)
            pytest.fail(f"API authentication failed - check DISCOVERY_API_KEY: {e}")
        raise

    # Verify results
    assert result is not None, "Result should not be None"
    assert result.run_id is not None, "Run ID should be set"
    assert result.status == "completed", f"Run should be completed, got status: {result.status}"

    # Verify we got patterns (at least one pattern should be found)
    assert result.patterns is not None, "Patterns should not be None"
    assert len(result.patterns) > 0, f"Should find at least one pattern, got {len(result.patterns)}"

    # Verify summary exists
    assert result.summary is not None, "Summary should not be None"

    # Verify feature importance exists (if available)
    # Note: Feature importance might be None in some cases, so we don't assert it exists


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_client_e2e_async_workflow(engine, test_dataframe, api_url):
    """
    Test async workflow: start analysis, then wait for completion separately.

    This tests the async pattern where you start a run and check status later.
    """
    try:
        # Start analysis without waiting
        result = await engine.run_async(
            file=test_dataframe,
            target_column="price",
            depth_iterations=1,
            auto_report_use_llm_evals=False,
            wait=False,  # Don't wait immediately
        )
    except Exception as e:
        error_str = str(e).lower()
        if (
            "401" in error_str
            or "403" in error_str
            or "unauthorized" in error_str
            or "forbidden" in error_str
        ):
            print_auth_error_warning(e, api_url)
            pytest.fail(f"API authentication failed - check DISCOVERY_API_KEY: {e}")
        raise

    assert result is not None, "Result should not be None"
    assert result.run_id is not None, "Run ID should be set"
    run_id = result.run_id

    # Now wait for completion separately
    completed_result = await engine.wait_for_completion(
        run_id=run_id,
        poll_interval=5.0,  # Check every 5 seconds
        timeout=600,  # 10 minute timeout
    )

    # Verify completion
    assert (
        completed_result.status == "completed"
    ), f"Run should be completed, got: {completed_result.status}"
    assert completed_result.patterns is not None, "Patterns should not be None"
    assert len(completed_result.patterns) > 0, "Should find at least one pattern"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_client_e2e_get_results(engine, test_dataframe, api_url):
    """
    Test getting results for an existing run.

    This tests the get_results method which can be used to check status
    of a run that was started elsewhere.
    """
    try:
        # Start a run
        result = await engine.run_async(
            file=test_dataframe,
            target_column="price",
            depth_iterations=1,
            auto_report_use_llm_evals=False,
            wait=False,
        )
    except Exception as e:
        error_str = str(e).lower()
        if (
            "401" in error_str
            or "403" in error_str
            or "unauthorized" in error_str
            or "forbidden" in error_str
        ):
            print_auth_error_warning(e, api_url)
            pytest.fail(f"API authentication failed - check DISCOVERY_API_KEY: {e}")
        raise

    run_id = result.run_id

    # Get results immediately (might still be processing)
    initial_result = await engine.get_results(run_id)
    assert initial_result is not None, "Should get initial result"
    assert initial_result.run_id == run_id, "Run ID should match"

    # Wait for completion
    final_result = await engine.wait_for_completion(run_id, timeout=600)

    # Verify final results
    assert final_result.status == "completed", "Run should complete"
    assert final_result.patterns is not None, "Patterns should be available"
    assert len(final_result.patterns) > 0, "Should find patterns"
