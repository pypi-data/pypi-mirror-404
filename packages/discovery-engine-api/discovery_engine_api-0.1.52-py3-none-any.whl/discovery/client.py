"""Discovery Engine Python SDK."""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx

try:
    import pandas as pd
except ImportError:
    pd = None

from discovery.types import (
    Column,
    CorrelationEntry,
    DataInsights,
    EngineResult,
    FeatureImportance,
    FeatureImportanceScore,
    FileInfo,
    Pattern,
    PatternGroup,
    RunStatus,
    Summary,
)


class Engine:
    """Engine for the Discovery Engine API."""

    # Production API URL (can be overridden via DISCOVERY_API_URL env var for testing)
    # This points to the Modal-deployed FastAPI API
    _DEFAULT_BASE_URL = "https://leap-labs-production--discovery-api.modal.run"

    # Dashboard URL for web UI and /api/* endpoints
    _DEFAULT_DASHBOARD_URL = "https://disco.leap-labs.com"

    def __init__(self, api_key: str):
        """
        Initialize the Discovery Engine.

        Args:
            api_key: Your API key
        """

        print("Initializing Discovery Engine...")
        self.api_key = api_key
        # Use DISCOVERY_API_URL env var if set (for testing/custom deployments),
        # otherwise use the production default
        self.base_url = os.getenv("DISCOVERY_API_URL", self._DEFAULT_BASE_URL).rstrip("/")
        # Dashboard URL for /api/* endpoints and web UI links
        self.dashboard_url = os.getenv(
            "DISCOVERY_DASHBOARD_URL", self._DEFAULT_DASHBOARD_URL
        ).rstrip("/")
        self._organization_id: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._dashboard_client: Optional[httpx.AsyncClient] = None
        self._org_fetched = False

    async def _ensure_organization_id(self) -> str:
        """
        Ensure we have an organization ID, fetching from API if needed.

        The organization ID is required for API requests to identify which
        organization the user belongs to (multi-tenancy support).

        Returns:
            Organization ID string

        Raises:
            ValueError: If no organization is found or API request fails
        """
        if self._organization_id:
            return self._organization_id

        if not self._org_fetched:
            # Fetch user's organizations and use the first one
            try:
                orgs = await self.get_organizations()
                if orgs:
                    self._organization_id = orgs[0]["id"]
            except ValueError as e:
                # Re-raise with more context
                raise ValueError(
                    f"Failed to fetch organization: {e}. "
                    "Please ensure your API key is valid and you belong to an organization."
                ) from e
            self._org_fetched = True

        if not self._organization_id:
            raise ValueError(
                "No organization found for your account. "
                "Please contact support if this issue persists."
            )

        return self._organization_id

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=60.0,
            )
        return self._client

    async def _get_client_with_org(self) -> httpx.AsyncClient:
        """
        Get HTTP client with organization header set.

        The organization ID is required for API requests to identify which
        organization the user belongs to (multi-tenancy support).
        """
        client = await self._get_client()

        # Ensure we have an organization ID
        org_id = await self._ensure_organization_id()

        # Set the organization header
        client.headers["X-Organization-ID"] = org_id

        return client

    async def _get_dashboard_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client for dashboard API calls."""
        if self._dashboard_client is None:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            self._dashboard_client = httpx.AsyncClient(
                base_url=self.dashboard_url,
                headers=headers,
                timeout=60.0,
            )
        return self._dashboard_client

    async def close(self):
        """Close the HTTP clients."""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._dashboard_client:
            await self._dashboard_client.aclose()
            self._dashboard_client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def get_organizations(self) -> List[Dict[str, Any]]:
        """
        Get the organizations you belong to.

        Returns:
            List of organizations with id, name, and slug

        Raises:
            ValueError: If the API request fails
        """
        client = await self._get_client()

        try:
            response = await client.get("/v1/me/organizations")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"Failed to fetch organizations: {e.response.status_code} {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise ValueError(f"Failed to connect to API: {str(e)}") from e

    async def upload_file(
        self, file: Union[str, Path, "pd.DataFrame"], filename: Optional[str] = None
    ) -> FileInfo:
        """
        Upload a file to the API.

        Args:
            file: File path, Path object, or pandas DataFrame
            filename: Optional filename (for DataFrame uploads)

        Returns:
            FileInfo with file_path, file_hash, file_size, mime_type
        """
        client = await self._get_client_with_org()

        if pd is not None and isinstance(file, pd.DataFrame):
            # Convert DataFrame to CSV in memory
            import io

            buffer = io.BytesIO()
            file.to_csv(buffer, index=False)
            buffer.seek(0)
            file_content = buffer.getvalue()
            filename = filename or "dataset.csv"
            mime_type = "text/csv"
        else:
            # Read file from disk
            file_path = Path(file)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            file_content = file_path.read_bytes()
            filename = filename or file_path.name
            mime_type = (
                "text/csv" if file_path.suffix == ".csv" else "application/vnd.apache.parquet"
            )

        # Upload file
        files = {"file": (filename, file_content, mime_type)}
        response = await client.post("/v1/upload", files=files)
        response.raise_for_status()

        data = response.json()
        return FileInfo(
            file_path=data["file_path"],
            file_hash=data["file_hash"],
            file_size=data["file_size"],
            mime_type=data["mime_type"],
        )

    async def create_dataset(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        total_rows: int = 0,
        dataset_size_mb: Optional[float] = None,
        author: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a dataset record.

        Args:
            title: Dataset title
            description: Dataset description
            total_rows: Number of rows in the dataset
            dataset_size_mb: Dataset size in MB
            author: Optional author attribution
            source_url: Optional source URL

        Returns:
            Dataset record with ID
        """
        client = await self._get_client_with_org()

        response = await client.post(
            "/v1/run-datasets",
            json={
                "title": title,
                "description": description,
                "total_rows": total_rows,
                "dataset_size_mb": dataset_size_mb,
                "author": author,
                "source_url": source_url,
            },
        )
        response.raise_for_status()
        return response.json()

    async def create_file_record(self, dataset_id: str, file_info: FileInfo) -> Dict[str, Any]:
        """
        Create a file record for a dataset.

        Args:
            dataset_id: Dataset ID
            file_info: FileInfo from upload_file()

        Returns:
            File record with ID
        """
        client = await self._get_client_with_org()

        response = await client.post(
            f"/v1/run-datasets/{dataset_id}/files",
            json={
                "mime_type": file_info.mime_type,
                "file_path": file_info.file_path,
                "file_hash": file_info.file_hash,
                "file_size": file_info.file_size,
            },
        )
        response.raise_for_status()
        return response.json()

    async def create_columns(
        self, dataset_id: str, columns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create column records for a dataset.

        Args:
            dataset_id: Dataset ID
            columns: List of column definitions with full metadata

        Returns:
            List of column records with IDs
        """
        client = await self._get_client_with_org()

        response = await client.post(
            f"/v1/run-datasets/{dataset_id}/columns",
            json=columns,
        )
        response.raise_for_status()
        return response.json()

    async def create_run(
        self,
        dataset_id: str,
        target_column_id: str,
        task: str = "regression",
        depth_iterations: int = 1,
        visibility: str = "public",
        timeseries_groups: Optional[List[Dict[str, Any]]] = None,
        target_column_override: Optional[str] = None,
        auto_report_use_llm_evals: bool = True,
        author: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a run and enqueue it for processing.

        Args:
            dataset_id: Dataset ID
            target_column_id: Target column ID
            task: Task type (regression, binary_classification, multiclass_classification)
            depth_iterations: Number of iterative feature removal cycles (1 = fastest)
            visibility: Dataset visibility ("public" or "private")
            timeseries_groups: Optional list of timeseries column groups
            target_column_override: Optional override for target column name
            auto_report_use_llm_evals: Use LLM evaluations
            author: Optional dataset author
            source_url: Optional source URL

        Returns:
            Run record with ID and job information
        """
        client = await self._get_client_with_org()

        payload = {
            "run_target_column_id": target_column_id,
            "task": task,
            "depth_iterations": depth_iterations,
            "visibility": visibility,
            "auto_report_use_llm_evals": auto_report_use_llm_evals,
        }

        if timeseries_groups:
            payload["timeseries_groups"] = timeseries_groups
        if target_column_override:
            payload["target_column_override"] = target_column_override
        if author:
            payload["author"] = author
        if source_url:
            payload["source_url"] = source_url

        response = await client.post(
            f"/v1/run-datasets/{dataset_id}/runs",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def get_results(self, run_id: str) -> EngineResult:
        """
        Get complete analysis results for a run.

        This returns all data that the Discovery dashboard displays:
        - LLM-generated summary with key insights
        - All discovered patterns with conditions, citations, and explanations
        - Column/feature information with statistics and importance scores
        - Correlation matrix
        - Global feature importance

        Args:
            run_id: The run ID

        Returns:
            EngineResult with complete analysis data
        """
        # Use dashboard client for /api/* endpoints (hosted on Next.js dashboard, not Modal API)
        dashboard_client = await self._get_dashboard_client()

        # Call dashboard API for results
        response = await dashboard_client.get(f"/api/runs/{run_id}/results")
        response.raise_for_status()

        data = response.json()
        return self._parse_analysis_result(data)

    async def get_run_status(self, run_id: str) -> RunStatus:
        """
        Get the status of a run.

        Args:
            run_id: Run ID

        Returns:
            RunStatus with current status information
        """
        client = await self._get_client_with_org()

        response = await client.get(f"/v1/runs/{run_id}/results")
        response.raise_for_status()

        data = response.json()
        return RunStatus(
            run_id=data["run_id"],
            status=data["status"],
            job_id=data.get("job_id"),
            job_status=data.get("job_status"),
            error_message=data.get("error_message"),
        )

    async def wait_for_completion(
        self,
        run_id: str,
        poll_interval: float = 5.0,
        timeout: Optional[float] = None,
    ) -> EngineResult:
        """
        Wait for a run to complete and return the results.

        Args:
            run_id: Run ID
            poll_interval: Seconds between status checks (default: 5)
            timeout: Maximum seconds to wait (None = no timeout)

        Returns:
            EngineResult with complete analysis data

        Raises:
            TimeoutError: If the run doesn't complete within the timeout
            RuntimeError: If the run fails
        """
        start_time = time.time()
        last_status = None
        poll_count = 0

        print(f"⏳ Waiting for run {run_id} to complete...")

        while True:
            result = await self.get_results(run_id)
            elapsed = time.time() - start_time
            poll_count += 1

            # Log status changes or every 3rd poll (every ~15 seconds)
            if result.status != last_status or poll_count % 3 == 0:
                status_msg = f"Status: {result.status}"
                if result.job_status:
                    status_msg += f" (job: {result.job_status})"
                if elapsed > 0:
                    status_msg += f" | Elapsed: {elapsed:.1f}s"
                print(f"  {status_msg}")

            last_status = result.status

            if result.status == "completed":
                print(f"✓ Run completed in {elapsed:.1f}s")
                return result
            elif result.status == "failed":
                error_msg = result.error_message or "Unknown error"
                print(f"✗ Run failed: {error_msg}")
                raise RuntimeError(f"Run {run_id} failed: {error_msg}")

            if timeout and elapsed > timeout:
                raise TimeoutError(f"Run {run_id} did not complete within {timeout} seconds")

            await asyncio.sleep(poll_interval)

    async def run_async(
        self,
        file: Union[str, Path, "pd.DataFrame"],
        target_column: str,
        depth_iterations: int = 1,
        title: Optional[str] = None,
        description: Optional[str] = None,
        column_descriptions: Optional[Dict[str, str]] = None,
        excluded_columns: Optional[List[str]] = None,
        task: Optional[str] = None,
        visibility: str = "public",
        timeseries_groups: Optional[List[Dict[str, Any]]] = None,
        target_column_override: Optional[str] = None,
        auto_report_use_llm_evals: bool = True,
        author: Optional[str] = None,
        source_url: Optional[str] = None,
        wait: bool = False,
        wait_timeout: Optional[float] = None,
        **kwargs,
    ) -> EngineResult:
        """
        Run analysis on a dataset (async).

        This method calls the dashboard API which handles the entire workflow:
        file upload, dataset creation, column inference, run creation, and credit deduction.

        Args:
            file: File path, Path object, or pandas DataFrame
            target_column: Name of the target column
            depth_iterations: Number of iterative feature removal cycles (1 = fastest)
            title: Optional dataset title
            description: Optional dataset description
            column_descriptions: Optional dict mapping column names to descriptions
            excluded_columns: Optional list of column names to exclude from analysis
            task: Task type (regression, binary, multiclass) - auto-detected if None
            visibility: Dataset visibility ("public" or "private", default: "public")
            timeseries_groups: Optional list of timeseries column groups
            target_column_override: Optional override for target column name
            auto_report_use_llm_evals: Use LLM evaluations (default: True)
            author: Optional dataset author
            source_url: Optional source URL
            wait: If True, wait for analysis to complete and return full results
            wait_timeout: Maximum seconds to wait for completion (only if wait=True)

        Returns:
            EngineResult with run_id and (if wait=True) complete results
        """
        # Prepare file for upload
        if pd is not None and isinstance(file, pd.DataFrame):
            # Convert DataFrame to CSV in memory
            import io

            print(f"📊 Preparing DataFrame ({len(file)} rows, {len(file.columns)} columns)...")
            buffer = io.BytesIO()
            file.to_csv(buffer, index=False)
            buffer.seek(0)
            file_content = buffer.getvalue()
            filename = (title + ".csv") if title else "dataset.csv"
            mime_type = "text/csv"
            file_size_mb = len(file_content) / (1024 * 1024)
            print(f"  File size: {file_size_mb:.2f} MB")
        else:
            # Read file from disk
            file_path = Path(file)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            print(f"📁 Reading file: {file_path.name}...")
            file_content = file_path.read_bytes()
            filename = file_path.name
            mime_type = (
                "text/csv" if file_path.suffix == ".csv" else "application/vnd.apache.parquet"
            )
            file_size_mb = len(file_content) / (1024 * 1024)
            print(f"  File size: {file_size_mb:.2f} MB")

        # Prepare multipart form data
        files = {"file": (filename, file_content, mime_type)}
        data: Dict[str, Any] = {
            "target_column": target_column,
            "depth_iterations": str(depth_iterations),
            "visibility": visibility,
        }

        if description:
            data["description"] = description
        if author:
            data["author"] = author
        if source_url:
            data["source_url"] = source_url
        if column_descriptions:
            data["column_descriptions"] = json.dumps(column_descriptions)
        if excluded_columns:
            data["excluded_columns"] = json.dumps(excluded_columns)
        if timeseries_groups:
            data["timeseries_groups"] = json.dumps(timeseries_groups)

        # Call dashboard API to create report
        print(
            f"🚀 Uploading file and creating run (depth: {depth_iterations}, target: {target_column})..."
        )
        # Use dashboard client for /api/* endpoints (hosted on Next.js dashboard, not Modal API)
        dashboard_client = await self._get_dashboard_client()
        # httpx automatically handles multipart/form-data when both files and data are provided
        response = await dashboard_client.post("/api/reports/create", files=files, data=data)
        response.raise_for_status()

        result_data = response.json()

        # Check if duplicate
        if result_data.get("duplicate"):
            # For duplicates, get the run_id and fetch results
            report_id = result_data.get("report_id")
            run_id = result_data.get("run_id")

            if not report_id or not run_id:
                raise ValueError("Duplicate report found but missing report_id or run_id")

            print(f"ℹ️  Duplicate report found (run_id: {run_id})")

            # Construct dashboard URL for the processing page
            progress_url = f"{self.dashboard_url}/reports/new/{run_id}/processing"
            print(f"🔗 View progress: {progress_url}")

            # If wait is True, fetch the full results for the existing report
            if wait:
                return await self.get_results(run_id)

            # Otherwise return a minimal result with the run_id
            return EngineResult(
                run_id=run_id,
                status="completed",
                report_id=report_id,
            )

        run_id = result_data["run_id"]
        print(f"✓ Run created: {run_id}")

        # Construct dashboard URL for the processing page
        progress_url = f"{self.dashboard_url}/reports/new/{run_id}/processing"
        print(f"🔗 View progress: {progress_url}")

        if wait:
            # Wait for completion and return full results
            return await self.wait_for_completion(run_id, timeout=wait_timeout)

        # Return minimal result with pending status
        return EngineResult(
            run_id=run_id,
            status="pending",
        )

    def run(
        self,
        file: Union[str, Path, "pd.DataFrame"],
        target_column: str,
        depth_iterations: int = 1,
        title: Optional[str] = None,
        description: Optional[str] = None,
        column_descriptions: Optional[Dict[str, str]] = None,
        excluded_columns: Optional[List[str]] = None,
        task: Optional[str] = None,
        visibility: str = "public",
        timeseries_groups: Optional[List[Dict[str, Any]]] = None,
        target_column_override: Optional[str] = None,
        auto_report_use_llm_evals: bool = True,
        author: Optional[str] = None,
        source_url: Optional[str] = None,
        wait: bool = False,
        wait_timeout: Optional[float] = None,
        **kwargs,
    ) -> EngineResult:
        """
        Run analysis on a dataset (synchronous wrapper).

        This is a synchronous wrapper around run_async().

        Args:
            file: File path, Path object, or pandas DataFrame
            target_column: Name of the target column
            depth_iterations: Number of iterative feature removal cycles (1 = fastest)
            title: Optional dataset title
            description: Optional dataset description
            column_descriptions: Optional dict mapping column names to descriptions
            excluded_columns: Optional list of column names to exclude from analysis
            task: Task type (regression, binary_classification, multiclass_classification) - auto-detected if None
            visibility: Dataset visibility ("public" or "private", default: "public")
            timeseries_groups: Optional list of timeseries column groups
            target_column_override: Optional override for target column name
            auto_report_use_llm_evals: Use LLM evaluations (default: True)
            author: Optional dataset author
            source_url: Optional source URL
            wait: If True, wait for analysis to complete and return full results
            wait_timeout: Maximum seconds to wait for completion (only if wait=True)
            **kwargs: Additional arguments passed to run_async()

        Returns:
            EngineResult with run_id and (if wait=True) complete results
        """
        coro = self.run_async(
            file,
            target_column,
            depth_iterations,
            title=title,
            description=description,
            column_descriptions=column_descriptions,
            excluded_columns=excluded_columns,
            task=task,
            visibility=visibility,
            timeseries_groups=timeseries_groups,
            target_column_override=target_column_override,
            auto_report_use_llm_evals=auto_report_use_llm_evals,
            author=author,
            source_url=source_url,
            wait=wait,
            wait_timeout=wait_timeout,
            **kwargs,
        )

        # Try to run the coroutine
        # If we're in a Jupyter notebook with a running event loop, asyncio.run() will fail
        try:
            return asyncio.run(coro)
        except RuntimeError as e:
            # Check if the error is about a running event loop
            if "cannot be called from a running event loop" in str(e).lower():
                # We're in a Jupyter/IPython environment with a running event loop
                # Try to use nest_asyncio if available
                try:
                    import nest_asyncio

                    # Apply nest_asyncio (it's safe to call multiple times)
                    nest_asyncio.apply()
                    # Now we can use asyncio.run() even with a running loop
                    return asyncio.run(coro)
                except ImportError:
                    raise RuntimeError(
                        "Cannot use engine.run() in a Jupyter notebook or environment with a running event loop. "
                        "Please use 'await engine.run_async(...)' instead, or install nest_asyncio "
                        "(pip install nest-asyncio) to enable nested event loops."
                    ) from e
            # Re-raise if it's a different RuntimeError
            raise

    def _parse_analysis_result(self, data: Dict[str, Any]) -> EngineResult:
        """Parse API response into EngineResult dataclass."""
        # Parse summary
        summary = None
        if data.get("summary"):
            summary = self._parse_summary(data["summary"])

        # Parse patterns
        patterns = []
        for p in data.get("patterns", []):
            patterns.append(
                Pattern(
                    id=p["id"],
                    task=p.get("task", "regression"),
                    target_column=p.get("target_column", ""),
                    direction=p.get("direction", "max"),
                    p_value=p.get("p_value", 0),
                    conditions=p.get("conditions", []),
                    lift_value=p.get("lift_value", 0),
                    support_count=p.get("support_count", 0),
                    support_percentage=p.get("support_percentage", 0),
                    pattern_type=p.get("pattern_type", "validated"),
                    novelty_type=p.get("novelty_type", "confirmatory"),
                    target_score=p.get("target_score", 0),
                    target_class=p.get("target_class"),
                    target_mean=p.get("target_mean"),
                    target_std=p.get("target_std"),
                    description=p.get("description", ""),
                    novelty_explanation=p.get("novelty_explanation", ""),
                    citations=p.get("citations", []),
                )
            )

        # Parse columns
        columns = []
        for c in data.get("columns", []):
            columns.append(
                Column(
                    id=c["id"],
                    name=c["name"],
                    display_name=c.get("display_name", c["name"]),
                    type=c.get("type", "continuous"),
                    data_type=c.get("data_type", "float"),
                    enabled=c.get("enabled", True),
                    description=c.get("description"),
                    mean=c.get("mean"),
                    median=c.get("median"),
                    std=c.get("std"),
                    min=c.get("min"),
                    max=c.get("max"),
                    iqr_min=c.get("iqr_min"),
                    iqr_max=c.get("iqr_max"),
                    mode=c.get("mode"),
                    approx_unique=c.get("approx_unique"),
                    null_percentage=c.get("null_percentage"),
                    feature_importance_score=c.get("feature_importance_score"),
                )
            )

        # Parse correlation matrix
        correlation_matrix = []
        for entry in data.get("correlation_matrix", []):
            correlation_matrix.append(
                CorrelationEntry(
                    feature_x=entry["feature_x"],
                    feature_y=entry["feature_y"],
                    value=entry["value"],
                )
            )

        # Parse feature importance
        feature_importance = None
        if data.get("feature_importance"):
            fi = data["feature_importance"]
            scores = [
                FeatureImportanceScore(feature=s["feature"], score=s["score"])
                for s in fi.get("scores", [])
            ]
            feature_importance = FeatureImportance(
                kind=fi.get("kind", "global"),
                baseline=fi.get("baseline", 0),
                scores=scores,
            )

        return EngineResult(
            run_id=data["run_id"],
            report_id=data.get("report_id"),
            status=data.get("status", "unknown"),
            dataset_title=data.get("dataset_title"),
            dataset_description=data.get("dataset_description"),
            total_rows=data.get("total_rows"),
            target_column=data.get("target_column"),
            task=data.get("task"),
            summary=summary,
            patterns=patterns,
            columns=columns,
            correlation_matrix=correlation_matrix,
            feature_importance=feature_importance,
            job_id=data.get("job_id"),
            job_status=data.get("job_status"),
            error_message=data.get("error_message"),
        )

    def _parse_summary(self, data: Dict[str, Any]) -> Summary:
        """Parse summary data into Summary dataclass."""
        # Parse data insights
        data_insights = None
        if data.get("data_insights"):
            di = data["data_insights"]
            data_insights = DataInsights(
                important_features=di.get("important_features", []),
                important_features_explanation=di.get("important_features_explanation", ""),
                strong_correlations=di.get("strong_correlations", []),
                strong_correlations_explanation=di.get("strong_correlations_explanation", ""),
                notable_relationships=di.get("notable_relationships", []),
            )

        return Summary(
            overview=data.get("overview", ""),
            key_insights=data.get("key_insights", []),
            novel_patterns=PatternGroup(
                pattern_ids=data.get("novel_patterns", {}).get("pattern_ids", []),
                explanation=data.get("novel_patterns", {}).get("explanation", ""),
            ),
            surprising_findings=PatternGroup(
                pattern_ids=data.get("surprising_findings", {}).get("pattern_ids", []),
                explanation=data.get("surprising_findings", {}).get("explanation", ""),
            ),
            statistically_significant=PatternGroup(
                pattern_ids=data.get("statistically_significant", {}).get("pattern_ids", []),
                explanation=data.get("statistically_significant", {}).get("explanation", ""),
            ),
            data_insights=data_insights,
            selected_pattern_id=data.get("selected_pattern_id"),
        )
