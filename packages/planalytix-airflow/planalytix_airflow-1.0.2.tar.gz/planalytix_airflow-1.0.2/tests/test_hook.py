"""
Unit tests for PlanalytixHook.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import requests

# Import after mocking to avoid Airflow dependency issues in tests
with patch.dict("sys.modules", {"airflow.hooks.base": MagicMock()}):
    from planalytix_provider.hooks.planalytix import PlanalytixHook


class TestPlanalytixHookInit:
    """Tests for PlanalytixHook initialization."""
    
    def test_default_connection_id(self):
        """Test default connection ID is set."""
        hook = PlanalytixHook()
        assert hook.planalytix_conn_id == "planalytix_default"
    
    def test_custom_connection_id(self):
        """Test custom connection ID is used."""
        hook = PlanalytixHook(planalytix_conn_id="my_connection")
        assert hook.planalytix_conn_id == "my_connection"
    
    def test_direct_api_key(self):
        """Test direct API key override."""
        hook = PlanalytixHook(api_key="flx_direct_key")
        assert hook._api_key == "flx_direct_key"
    
    def test_direct_base_url(self):
        """Test direct base URL override."""
        hook = PlanalytixHook(base_url="https://custom.api.com")
        assert hook._base_url == "https://custom.api.com"


class TestPlanalytixHookSession:
    """Tests for session creation and configuration."""
    
    @patch.object(PlanalytixHook, "get_connection")
    def test_session_created_with_auth_header(self, mock_get_conn):
        """Test session includes Authorization header."""
        mock_get_conn.return_value = MagicMock(
            host="https://api.planalytix.io",
            password="flx_test_key",
            extra_dejson={},
        )
        
        hook = PlanalytixHook()
        session = hook.get_conn()
        
        assert "Authorization" in session.headers
        assert session.headers["Authorization"] == "Bearer flx_test_key"
    
    @patch.object(PlanalytixHook, "get_connection")
    def test_session_content_type_header(self, mock_get_conn):
        """Test session includes Content-Type header."""
        mock_get_conn.return_value = MagicMock(
            host="https://api.planalytix.io",
            password="flx_test_key",
            extra_dejson={},
        )
        
        hook = PlanalytixHook()
        session = hook.get_conn()
        
        assert session.headers["Content-Type"] == "application/json"
    
    @patch.object(PlanalytixHook, "get_connection")
    def test_session_user_agent_header(self, mock_get_conn):
        """Test session includes User-Agent header."""
        mock_get_conn.return_value = MagicMock(
            host="https://api.planalytix.io",
            password="flx_test_key",
            extra_dejson={},
        )
        
        hook = PlanalytixHook()
        session = hook.get_conn()
        
        assert "planalytix-airflow" in session.headers["User-Agent"]
    
    @patch.object(PlanalytixHook, "get_connection")
    def test_session_org_id_from_extra(self, mock_get_conn):
        """Test organization ID is added from extras."""
        mock_get_conn.return_value = MagicMock(
            host="https://api.planalytix.io",
            password="flx_test_key",
            extra_dejson={"organization_id": "org_xyz"},
        )
        
        hook = PlanalytixHook()
        session = hook.get_conn()
        
        assert session.headers["X-Organization-ID"] == "org_xyz"
    
    @patch.object(PlanalytixHook, "get_connection")
    def test_base_url_normalized(self, mock_get_conn):
        """Test base URL trailing slash is removed."""
        mock_get_conn.return_value = MagicMock(
            host="https://api.planalytix.io/",
            password="flx_test_key",
            extra_dejson={},
        )
        
        hook = PlanalytixHook()
        hook.get_conn()
        
        assert hook._base_url == "https://api.planalytix.io"
    
    @patch.object(PlanalytixHook, "get_connection")
    def test_base_url_https_added(self, mock_get_conn):
        """Test https:// is added if missing."""
        mock_get_conn.return_value = MagicMock(
            host="api.planalytix.io",
            password="flx_test_key",
            extra_dejson={},
        )
        
        hook = PlanalytixHook()
        hook.get_conn()
        
        assert hook._base_url == "https://api.planalytix.io"


class TestPlanalytixHookTriggerSync:
    """Tests for trigger_sync method."""
    
    @patch.object(PlanalytixHook, "get_connection")
    @patch.object(PlanalytixHook, "get_conn")
    def test_trigger_sync_basic(
        self, mock_get_conn, mock_get_connection, sample_job_response
    ):
        """Test basic sync trigger."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = sample_job_response
        mock_session.post.return_value = mock_response
        mock_get_conn.return_value = mock_session
        
        hook = PlanalytixHook()
        hook._base_url = "https://api.planalytix.io"
        
        result = hook.trigger_sync(connection_id="conn_xyz789")
        
        assert result["job_id"] == "job_abc123"
        assert result["status"] == "queued"
        mock_session.post.assert_called_once()
    
    @patch.object(PlanalytixHook, "get_connection")
    @patch.object(PlanalytixHook, "get_conn")
    def test_trigger_sync_with_options(self, mock_get_conn, mock_get_connection):
        """Test sync trigger with all options."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"job_id": "job_123", "status": "queued"}
        mock_session.post.return_value = mock_response
        mock_get_conn.return_value = mock_session
        
        hook = PlanalytixHook()
        hook._base_url = "https://api.planalytix.io"
        
        hook.trigger_sync(
            connection_id="conn_xyz",
            sync_type="full",
            streams=["orders", "customers"],
            priority="high",
            metadata={"dag_id": "test_dag"},
            idempotency_key="idem_123",
        )
        
        call_args = mock_session.post.call_args
        payload = call_args.kwargs["json"]
        
        assert payload["sync_type"] == "full"
        assert payload["streams"] == ["orders", "customers"]
        assert payload["priority"] == "high"
        assert payload["metadata"] == {"dag_id": "test_dag"}
        assert payload["idempotency_key"] == "idem_123"
    
    @patch.object(PlanalytixHook, "get_connection")
    @patch.object(PlanalytixHook, "get_conn")
    def test_trigger_sync_conflict(self, mock_get_conn, mock_get_connection):
        """Test handling of sync already in progress (409)."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.json.return_value = {
            "error": "Sync already in progress",
            "existing_job_id": "job_existing",
        }
        mock_session.post.return_value = mock_response
        mock_get_conn.return_value = mock_session
        
        hook = PlanalytixHook()
        hook._base_url = "https://api.planalytix.io"
        
        result = hook.trigger_sync(connection_id="conn_xyz")
        
        assert result["existing_job_id"] == "job_existing"


class TestPlanalytixHookGetJob:
    """Tests for get_job method."""
    
    @patch.object(PlanalytixHook, "get_connection")
    @patch.object(PlanalytixHook, "get_conn")
    def test_get_job_running(
        self, mock_get_conn, mock_get_connection, sample_running_job
    ):
        """Test getting a running job."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = sample_running_job
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_conn.return_value = mock_session
        
        hook = PlanalytixHook()
        hook._base_url = "https://api.planalytix.io"
        
        result = hook.get_job("job_abc123")
        
        assert result["status"] == "running"
        assert result["progress"]["rows_synced"] == 15420
    
    @patch.object(PlanalytixHook, "get_connection")
    @patch.object(PlanalytixHook, "get_conn")
    def test_get_job_completed(
        self, mock_get_conn, mock_get_connection, sample_completed_job
    ):
        """Test getting a completed job."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = sample_completed_job
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_conn.return_value = mock_session
        
        hook = PlanalytixHook()
        hook._base_url = "https://api.planalytix.io"
        
        result = hook.get_job("job_abc123")
        
        assert result["status"] == "completed"


class TestPlanalytixHookGetJobResults:
    """Tests for get_job_results method."""
    
    @patch.object(PlanalytixHook, "get_connection")
    @patch.object(PlanalytixHook, "get_conn")
    def test_get_job_results(
        self, mock_get_conn, mock_get_connection, sample_job_results
    ):
        """Test getting job results."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = sample_job_results
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_conn.return_value = mock_session
        
        hook = PlanalytixHook()
        hook._base_url = "https://api.planalytix.io"
        
        result = hook.get_job_results("job_abc123")
        
        assert result["summary"]["total_rows_synced"] == 48291
        assert len(result["streams"]) == 5


class TestPlanalytixHookCancelJob:
    """Tests for cancel_job method."""
    
    @patch.object(PlanalytixHook, "get_connection")
    @patch.object(PlanalytixHook, "get_conn")
    def test_cancel_job(self, mock_get_conn, mock_get_connection):
        """Test cancelling a job."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "job_id": "job_abc123",
            "status": "cancelled",
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_response
        mock_get_conn.return_value = mock_session
        
        hook = PlanalytixHook()
        hook._base_url = "https://api.planalytix.io"
        
        result = hook.cancel_job("job_abc123")
        
        assert result["status"] == "cancelled"
        mock_session.post.assert_called_once()


class TestPlanalytixHookListJobs:
    """Tests for list_jobs method."""
    
    @patch.object(PlanalytixHook, "get_connection")
    @patch.object(PlanalytixHook, "get_conn")
    def test_list_jobs_default(
        self, mock_get_conn, mock_get_connection, sample_jobs_list
    ):
        """Test listing jobs with defaults."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = sample_jobs_list
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_conn.return_value = mock_session
        
        hook = PlanalytixHook()
        hook._base_url = "https://api.planalytix.io"
        
        result = hook.list_jobs()
        
        assert len(result["jobs"]) == 2
        assert result["total"] == 150
    
    @patch.object(PlanalytixHook, "get_connection")
    @patch.object(PlanalytixHook, "get_conn")
    def test_list_jobs_with_filters(self, mock_get_conn, mock_get_connection):
        """Test listing jobs with filters."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"jobs": [], "total": 0}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response
        mock_get_conn.return_value = mock_session
        
        hook = PlanalytixHook()
        hook._base_url = "https://api.planalytix.io"
        
        hook.list_jobs(status="running", connection_id="conn_xyz", limit=50, offset=10)
        
        call_args = mock_session.get.call_args
        params = call_args.kwargs["params"]
        
        assert params["status"] == "running"
        assert params["connection_id"] == "conn_xyz"
        assert params["limit"] == 50
        assert params["offset"] == 10


class TestPlanalytixHookTestConnection:
    """Tests for test_connection method."""
    
    @patch.object(PlanalytixHook, "list_jobs")
    def test_connection_success(self, mock_list_jobs):
        """Test successful connection test."""
        mock_list_jobs.return_value = {"jobs": [], "total": 0}
        
        hook = PlanalytixHook()
        success, message = hook.test_connection()
        
        assert success is True
        assert "successful" in message.lower()
    
    @patch.object(PlanalytixHook, "list_jobs")
    def test_connection_failure(self, mock_list_jobs):
        """Test failed connection test."""
        mock_list_jobs.side_effect = requests.exceptions.ConnectionError("Failed")
        
        hook = PlanalytixHook()
        success, message = hook.test_connection()
        
        assert success is False
        assert "failed" in message.lower()
