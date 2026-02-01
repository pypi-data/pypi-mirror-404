"""Tests for the Discovery Engine Python SDK."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from discovery.client import Engine
from discovery.types import (
    Column,
    EngineResult,
    FeatureImportance,
    FileInfo,
    Pattern,
    RunStatus,
    Summary,
)


@pytest.fixture
def api_key():
    """Test API key."""
    return "test-api-key-12345"


@pytest.fixture
def client(api_key):
    """Create an Engine instance for testing."""
    return Engine(api_key=api_key)


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.AsyncClient."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.headers = {}
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.fixture
def sample_organizations():
    """Sample organizations response."""
    return [
        {"id": "org-123", "name": "Test Org", "slug": "test-org"},
        {"id": "org-456", "name": "Another Org", "slug": "another-org"},
    ]


@pytest.fixture
def sample_file_info():
    """Sample file info response."""
    return {
        "file_path": "gs://bucket/path/to/file.csv",
        "file_hash": "abc123def456",
        "file_size": 1024,
        "mime_type": "text/csv",
    }


@pytest.fixture
def sample_dataset():
    """Sample dataset response."""
    return {"id": "dataset-123", "title": "Test Dataset"}


@pytest.fixture
def sample_columns():
    """Sample columns response."""
    return [
        {
            "id": "col-1",
            "name": "age",
            "display_name": "Age",
            "type": "continuous",
            "data_type": "int",
            "enabled": True,
        },
        {
            "id": "col-2",
            "name": "price",
            "display_name": "Price",
            "type": "continuous",
            "data_type": "float",
            "enabled": True,
        },
    ]


@pytest.fixture
def sample_run():
    """Sample run response."""
    return {
        "id": "run-123",
        "job_id": "job-123",
        "job_status": "pending",
    }


@pytest.fixture
def sample_results():
    """Sample analysis results response."""
    return {
        "run_id": "run-123",
        "report_id": "report-123",
        "status": "completed",
        "dataset_title": "Test Dataset",
        "dataset_description": "A test dataset",
        "total_rows": 1000,
        "target_column": "price",
        "task": "regression",
        "summary": {
            "overview": "This dataset shows interesting patterns",
            "key_insights": ["Insight 1", "Insight 2"],
            "novel_patterns": {"pattern_ids": ["pattern-1"], "explanation": "Novel patterns found"},
            "surprising_findings": {
                "pattern_ids": ["pattern-2"],
                "explanation": "Surprising findings",
            },
            "statistically_significant": {
                "pattern_ids": ["pattern-3"],
                "explanation": "Significant patterns",
            },
            "data_insights": {
                "important_features": ["age", "location"],
                "important_features_explanation": "Age and location are important",
                "strong_correlations": [{"feature1": "age", "feature2": "price"}],
                "strong_correlations_explanation": "Age correlates with price",
                "notable_relationships": ["Age affects price"],
            },
            "selected_pattern_id": "pattern-1",
        },
        "patterns": [
            {
                "id": "pattern-1",
                "task": "regression",
                "target_column": "price",
                "direction": "max",
                "p_value": 0.01,
                "conditions": [
                    {"type": "continuous", "feature": "age", "min_value": 30.0, "max_value": 50.0}
                ],
                "lift_value": 1.5,
                "support_count": 200,
                "support_percentage": 20.0,
                "pattern_type": "validated",
                "novelty_type": "novel",
                "target_score": 100.0,
                "description": "Higher prices for ages 30-50",
                "novelty_explanation": "This is a novel finding",
                "citations": [],
            }
        ],
        "columns": [
            {
                "id": "col-1",
                "name": "age",
                "display_name": "Age",
                "type": "continuous",
                "data_type": "int",
                "enabled": True,
                "mean": 40.0,
                "median": 39.0,
                "std": 10.0,
                "min": 20.0,
                "max": 60.0,
                "null_percentage": 0.05,
                "feature_importance_score": 0.8,
            }
        ],
        "correlation_matrix": [
            {"feature_x": "age", "feature_y": "price", "value": 0.75},
        ],
        "feature_importance": {
            "kind": "global",
            "baseline": 50.0,
            "scores": [{"feature": "age", "score": 0.8}, {"feature": "location", "score": 0.6}],
        },
        "job_id": "job-123",
        "job_status": "completed",
    }


class TestClientInitialization:
    """Test client initialization."""

    def test_init_with_api_key(self, api_key):
        """Test engine initialization with API key."""
        engine = Engine(api_key=api_key)
        assert engine.api_key == api_key
        assert engine.base_url == Engine._DEFAULT_BASE_URL
        assert engine._organization_id is None
        assert engine._client is None
        assert engine._org_fetched is False

    def test_init_sets_base_url(self, api_key):
        """Test that base URL is set correctly."""
        engine = Engine(api_key=api_key)
        # Should use the default production URL
        assert engine.base_url == Engine._DEFAULT_BASE_URL


class TestGetOrganizations:
    """Test get_organizations method."""

    @pytest.mark.asyncio
    async def test_get_organizations_success(self, client, mock_httpx_client, sample_organizations):
        """Test successful organization fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_organizations
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch.object(client, "_get_client", return_value=mock_httpx_client):
            result = await client.get_organizations()

        assert result == sample_organizations
        mock_httpx_client.get.assert_called_once_with("/v1/me/organizations")

    @pytest.mark.asyncio
    async def test_get_organizations_http_error(self, client, mock_httpx_client):
        """Test organization fetch with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)
        mock_httpx_client.get = AsyncMock(side_effect=error)

        with patch.object(client, "_get_client", return_value=mock_httpx_client):
            with pytest.raises(ValueError, match="Failed to fetch organizations"):
                await client.get_organizations()

    @pytest.mark.asyncio
    async def test_get_organizations_request_error(self, client, mock_httpx_client):
        """Test organization fetch with request error."""
        error = httpx.RequestError("Connection failed", request=MagicMock())
        mock_httpx_client.get = AsyncMock(side_effect=error)

        with patch.object(client, "_get_client", return_value=mock_httpx_client):
            with pytest.raises(ValueError, match="Failed to connect to API"):
                await client.get_organizations()


class TestEnsureOrganizationId:
    """Test _ensure_organization_id method."""

    @pytest.mark.asyncio
    async def test_ensure_organization_id_cached(self, client):
        """Test that organization ID is cached after first fetch."""
        client._organization_id = "org-123"

        result = await client._ensure_organization_id()
        assert result == "org-123"

    @pytest.mark.asyncio
    async def test_ensure_organization_id_fetches(
        self, client, mock_httpx_client, sample_organizations
    ):
        """Test that organization ID is fetched if not cached."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_organizations
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client", return_value=mock_httpx_client):
            result = await client._ensure_organization_id()

        assert result == "org-123"
        assert client._organization_id == "org-123"
        assert client._org_fetched is True

    @pytest.mark.asyncio
    async def test_ensure_organization_id_no_orgs(self, client, mock_httpx_client):
        """Test error when no organizations are found."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client", return_value=mock_httpx_client):
            with pytest.raises(ValueError, match="No organization found"):
                await client._ensure_organization_id()


class TestUploadFile:
    """Test upload_file method."""

    @pytest.mark.asyncio
    async def test_upload_file_from_path(
        self, client, mock_httpx_client, sample_file_info, tmp_path
    ):
        """Test uploading a file from a file path."""
        # Create a test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\n1,2\n3,4")

        mock_response = MagicMock()
        mock_response.json.return_value = sample_file_info
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.upload_file(str(test_file))

        assert isinstance(result, FileInfo)
        assert result.file_path == sample_file_info["file_path"]
        assert result.file_hash == sample_file_info["file_hash"]
        assert result.file_size == sample_file_info["file_size"]
        assert result.mime_type == sample_file_info["mime_type"]

        # Verify the upload was called with correct parameters
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "/v1/upload"
        assert "files" in call_args[1]

    @pytest.mark.asyncio
    async def test_upload_file_not_found(self, client, mock_httpx_client):
        """Test uploading a non-existent file."""
        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            with pytest.raises(FileNotFoundError):
                await client.upload_file("nonexistent.csv")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True, reason="pandas may not be available in test environment"
    )  # We'll handle pandas separately
    async def test_upload_file_dataframe(self, client, mock_httpx_client, sample_file_info):
        """Test uploading a pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")

        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        mock_response = MagicMock()
        mock_response.json.return_value = sample_file_info
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.upload_file(df, filename="custom.csv")

        assert isinstance(result, FileInfo)
        mock_httpx_client.post.assert_called_once()


class TestCreateDataset:
    """Test create_dataset method."""

    @pytest.mark.asyncio
    async def test_create_dataset_success(self, client, mock_httpx_client, sample_dataset):
        """Test successful dataset creation."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_dataset
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.create_dataset(
                title="Test Dataset",
                description="A test dataset",
                total_rows=1000,
            )

        assert result == sample_dataset
        mock_httpx_client.post.assert_called_once_with(
            "/v1/run-datasets",
            json={
                "title": "Test Dataset",
                "description": "A test dataset",
                "total_rows": 1000,
                "dataset_size_mb": None,
                "author": None,
                "source_url": None,
            },
        )


class TestCreateFileRecord:
    """Test create_file_record method."""

    @pytest.mark.asyncio
    async def test_create_file_record_success(self, client, mock_httpx_client, sample_file_info):
        """Test successful file record creation."""
        file_info = FileInfo(**sample_file_info)
        dataset_id = "dataset-123"
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "file-record-123"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.create_file_record(dataset_id, file_info)

        assert result == {"id": "file-record-123"}
        mock_httpx_client.post.assert_called_once_with(
            f"/v1/run-datasets/{dataset_id}/files",
            json={
                "mime_type": file_info.mime_type,
                "file_path": file_info.file_path,
                "file_hash": file_info.file_hash,
                "file_size": file_info.file_size,
            },
        )


class TestCreateColumns:
    """Test create_columns method."""

    @pytest.mark.asyncio
    async def test_create_columns_success(self, client, mock_httpx_client, sample_columns):
        """Test successful column creation."""
        dataset_id = "dataset-123"
        columns_data = [
            {
                "name": "age",
                "display_name": "Age",
                "type": "continuous",
                "data_type": "int",
                "enabled": True,
            }
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = sample_columns
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.create_columns(dataset_id, columns_data)

        assert result == sample_columns
        mock_httpx_client.post.assert_called_once_with(
            f"/v1/run-datasets/{dataset_id}/columns",
            json=columns_data,
        )


class TestCreateRun:
    """Test create_run method."""

    @pytest.mark.asyncio
    async def test_create_run_success(self, client, mock_httpx_client, sample_run):
        """Test successful run creation."""
        dataset_id = "dataset-123"
        target_column_id = "col-2"

        mock_response = MagicMock()
        mock_response.json.return_value = sample_run
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.create_run(
                dataset_id=dataset_id,
                target_column_id=target_column_id,
                task="regression",
                depth_iterations=1,
            )

        assert result == sample_run
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == f"/v1/run-datasets/{dataset_id}/runs"
        payload = call_args[1]["json"]
        assert payload["run_target_column_id"] == target_column_id
        assert payload["task"] == "regression"
        assert payload["depth_iterations"] == 1

    @pytest.mark.asyncio
    async def test_create_run_with_optional_params(self, client, mock_httpx_client, sample_run):
        """Test run creation with optional parameters."""
        dataset_id = "dataset-123"
        target_column_id = "col-2"
        timeseries_groups = [{"base_name": "ts", "columns": ["ts1", "ts2"]}]

        mock_response = MagicMock()
        mock_response.json.return_value = sample_run
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.create_run(
                dataset_id=dataset_id,
                target_column_id=target_column_id,
                task="regression",
                depth_iterations=1,
                timeseries_groups=timeseries_groups,
                target_column_override="price_override",
                author="Test Author",
                source_url="https://example.com",
            )

        assert result == sample_run
        payload = mock_httpx_client.post.call_args[1]["json"]
        assert payload["timeseries_groups"] == timeseries_groups
        assert payload["target_column_override"] == "price_override"
        assert payload["author"] == "Test Author"
        assert payload["source_url"] == "https://example.com"


class TestGetResults:
    """Test get_results method."""

    @pytest.mark.asyncio
    async def test_get_results_success(self, client, mock_httpx_client, sample_results):
        """Test successful results retrieval."""
        run_id = "run-123"

        mock_response = MagicMock()
        mock_response.json.return_value = sample_results
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.get_results(run_id)

        assert isinstance(result, EngineResult)
        assert result.run_id == run_id
        assert result.status == "completed"
        assert len(result.patterns) == 1
        assert len(result.columns) == 1
        assert result.summary is not None
        assert result.feature_importance is not None

    @pytest.mark.asyncio
    async def test_get_results_parsing(self, client, mock_httpx_client, sample_results):
        """Test that results are parsed correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_results
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.get_results("run-123")

        # Check pattern parsing
        assert len(result.patterns) == 1
        pattern = result.patterns[0]
        assert isinstance(pattern, Pattern)
        assert pattern.id == "pattern-1"
        assert pattern.direction == "max"

        # Check column parsing
        assert len(result.columns) == 1
        column = result.columns[0]
        assert isinstance(column, Column)
        assert column.name == "age"
        assert column.feature_importance_score == 0.8

        # Check summary parsing
        assert result.summary is not None
        assert isinstance(result.summary, Summary)
        assert len(result.summary.key_insights) == 2

        # Check feature importance parsing
        assert result.feature_importance is not None
        assert isinstance(result.feature_importance, FeatureImportance)
        assert len(result.feature_importance.scores) == 2


class TestGetRunStatus:
    """Test get_run_status method."""

    @pytest.mark.asyncio
    async def test_get_run_status_success(self, client, mock_httpx_client):
        """Test successful status retrieval."""
        run_id = "run-123"
        status_data = {
            "run_id": run_id,
            "status": "processing",
            "job_id": "job-123",
            "job_status": "running",
            "error_message": None,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = status_data
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.get_run_status(run_id)

        assert isinstance(result, RunStatus)
        assert result.run_id == run_id
        assert result.status == "processing"
        assert result.job_id == "job-123"
        assert result.job_status == "running"


class TestWaitForCompletion:
    """Test wait_for_completion method."""

    @pytest.mark.asyncio
    async def test_wait_for_completion_success(self, client, mock_httpx_client, sample_results):
        """Test waiting for completion when run completes."""
        run_id = "run-123"
        sample_results["status"] = "completed"

        mock_response = MagicMock()
        mock_response.json.return_value = sample_results
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            with patch.object(client, "get_results", return_value=EngineResult(**sample_results)):
                result = await client.wait_for_completion(run_id, poll_interval=0.1)

        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_wait_for_completion_failed(self, client, mock_httpx_client):
        """Test waiting for completion when run fails."""
        run_id = "run-123"
        failed_result = EngineResult(
            run_id=run_id,
            status="failed",
            error_message="Processing failed",
        )

        with patch.object(client, "get_results", return_value=failed_result):
            with pytest.raises(RuntimeError, match="Run .* failed"):
                await client.wait_for_completion(run_id, poll_interval=0.1)

    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self, client, mock_httpx_client):
        """Test waiting for completion with timeout."""
        run_id = "run-123"
        pending_result = EngineResult(run_id=run_id, status="processing")

        with patch.object(client, "get_results", return_value=pending_result):
            with pytest.raises(TimeoutError, match="did not complete within"):
                await client.wait_for_completion(run_id, poll_interval=0.1, timeout=0.2)


class TestRunAsync:
    """Test run_async method."""

    @pytest.mark.asyncio
    async def test_analyze_async_basic(
        self,
        client,
        mock_httpx_client,
        sample_file_info,
        sample_dataset,
        sample_columns,
        sample_run,
    ):
        """Test basic run_async workflow with DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")

        # Create a DataFrame
        df = pd.DataFrame({"age": [30, 40], "price": [100, 150]})

        # Mock the single /api/reports/create endpoint response
        mock_response_create = MagicMock()
        mock_response_create.json.return_value = {"run_id": sample_run["id"]}
        mock_response_create.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response_create)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = await client.run_async(
                file=df,
                target_column="price",
                depth_iterations=1,
            )

        assert isinstance(result, EngineResult)
        assert result.run_id == str(sample_run["id"])
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_analyze_async_with_wait(
        self,
        client,
        mock_httpx_client,
        sample_file_info,
        sample_dataset,
        sample_columns,
        sample_run,
        sample_results,
    ):
        """Test run_async with wait=True."""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")

        # Create a DataFrame
        df = pd.DataFrame({"age": [30, 40], "price": [100, 150]})

        # Mock the single /api/reports/create endpoint response
        mock_response_create = MagicMock()
        mock_response_create.json.return_value = {"run_id": sample_run["id"]}
        mock_response_create.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response_create)
        mock_httpx_client.headers = {}

        completed_result = EngineResult(**sample_results)

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            with patch.object(client, "wait_for_completion", return_value=completed_result):
                result = await client.run_async(
                    file=df,
                    target_column="price",
                    wait=True,
                )

        assert result.status == "completed"
        assert len(result.patterns) == 1

    @pytest.mark.asyncio
    async def test_analyze_async_missing_target_column(
        self, client, mock_httpx_client, sample_file_info, sample_dataset, sample_columns
    ):
        """Test run_async when target column is not found."""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")

        # Create a DataFrame
        df = pd.DataFrame({"age": [30, 40], "price": [100, 150]})

        # Mock API error response for missing target column
        mock_response_error = MagicMock()
        mock_response_error.status_code = 400
        mock_response_error.text = "Target column 'price' not found"
        error = httpx.HTTPStatusError(
            "Target column 'price' not found",
            request=MagicMock(),
            response=mock_response_error,
        )

        mock_httpx_client.post = AsyncMock(side_effect=error)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            with pytest.raises(httpx.HTTPStatusError):
                await client.run_async(
                    file=df,
                    target_column="price",
                )


class TestRun:
    """Test run (synchronous) method."""

    def test_analyze_sync(
        self,
        client,
        mock_httpx_client,
        sample_file_info,
        sample_dataset,
        sample_columns,
        sample_run,
    ):
        """Test synchronous analyze method."""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")

        # Create a DataFrame
        df = pd.DataFrame({"age": [30, 40], "price": [100, 150]})

        # Mock the single /api/reports/create endpoint response
        mock_response_create = MagicMock()
        mock_response_create.json.return_value = {"run_id": sample_run["id"]}
        mock_response_create.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response_create)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client_with_org", return_value=mock_httpx_client):
            result = client.run(
                file=df,
                target_column="price",
                depth_iterations=1,
            )

        assert isinstance(result, EngineResult)
        assert result.run_id == str(sample_run["id"])


class TestContextManager:
    """Test context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager(self, api_key):
        """Test that client can be used as async context manager."""
        mock_httpx_client = AsyncMock(spec=httpx.AsyncClient)
        mock_httpx_client.headers = {}
        mock_httpx_client.aclose = AsyncMock()

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            async with Engine(api_key=api_key) as client:
                # Trigger client creation by calling a method
                await client._get_client()
                assert client._client is not None

        # Engine should be closed after context exit
        mock_httpx_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_method(self, client, mock_httpx_client):
        """Test explicit close method."""
        client._client = mock_httpx_client

        await client.close()

        assert client._client is None
        mock_httpx_client.aclose.assert_called_once()


class TestGetClientWithOrg:
    """Test _get_client_with_org method."""

    @pytest.mark.asyncio
    async def test_get_client_with_org_sets_header(
        self, client, mock_httpx_client, sample_organizations
    ):
        """Test that organization header is set."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_organizations
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.headers = {}

        with patch.object(client, "_get_client", return_value=mock_httpx_client):
            result = await client._get_client_with_org()

        assert result == mock_httpx_client
        assert result.headers["X-Organization-ID"] == "org-123"
